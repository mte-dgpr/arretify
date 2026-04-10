#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import logging
import sys
from datetime import date as Date
from pathlib import Path
from typing import Type

import git
from dotenv import load_dotenv
from pydantic import BaseModel

from arretify.law_data.apis.mistral import initialize_mistral_client
from arretify.pipeline import (
    PipelineStep,
    is_ocr_files,
    load_ocr_files,
    load_pdf_file,
    run_pipeline,
)
from arretify.settings import Settings
from arretify.step_ocr import step_ocr
from arretify.step_segmentation import step_segmentation
from arretify.types import DocumentContext, SessionContext
from quality_evaluation import segmentation_in_sections, tables_detection
from quality_evaluation.types import (
    ComputeMetricsFunction,
    Experiment,
    ExperimentConfig,
    ExtractFunction,
    FileName,
    MetricName,
    MetricSummary,
    Run,
    RunSummary,
    T,
)

_LOGGER = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).parent.parent

ProcessedArretes = list[tuple[Path, DocumentContext]]
"""List of tuples containing (pdf_file_path, document_context) for each processed PDF."""

# -------------------- JSON I/O -------------------- #


def dump_json(output_json_path: Path, model: BaseModel) -> None:
    output_json_path.write_text(model.model_dump_json(indent=2), encoding="utf-8")


def load_json(json_path: Path, model_class: Type[T]) -> T:
    try:
        return model_class.model_validate_json(json_path.read_text(encoding="utf-8"))
    except Exception:
        _LOGGER.error(f"Error loading JSON from {json_path}")
        raise


# -------------------- Arretify helpers -------------------- #


def run_arretify_on_all_pdfs(
    session_context: SessionContext, input_dir: Path, ocr_cache_dir: Path | None
) -> ProcessedArretes:
    """
    Run Arretify pipeline on all PDFs in input directory, using cache for OCR when available.

    Returns list of tuples containing (pdf_file_path, document_context) for each processed PDF.
    """
    # Find all PDF files
    pdf_file_paths: list[Path] = []
    for path in input_dir.iterdir():
        if path.is_file() and path.suffix.lower() == ".pdf":
            pdf_file_paths.append(path)

    # Process each PDF
    processed: ProcessedArretes = []
    for pdf_file_path in sorted(pdf_file_paths):
        steps: list[PipelineStep] = [
            step_segmentation,
        ]
        ocr_document_dir = ocr_cache_dir / pdf_file_path.stem if ocr_cache_dir else None

        # If cache directory exists, load from cache and skip OCR step.
        if ocr_document_dir is not None and ocr_document_dir.exists():
            if not is_ocr_files(ocr_document_dir):
                raise ValueError(f"Cache path {ocr_document_dir} exists and is not a directory.")
            document_context = load_ocr_files(session_context, ocr_document_dir)
            _LOGGER.info(f"Loading OCR pages from cache directory for {pdf_file_path.name}")

        # Else perform OCR and optionally save to cache if directory is provided.
        else:
            if ocr_document_dir is not None:

                def step_ocr_with_cache(
                    document_context: DocumentContext,
                ) -> DocumentContext:
                    return step_ocr(
                        document_context=document_context,
                        ocr_document_dir=ocr_document_dir,
                    )

                steps.insert(0, step_ocr_with_cache)
                ocr_document_dir.mkdir(parents=True, exist_ok=True)
            else:
                steps.insert(0, step_ocr)

            document_context = load_pdf_file(session_context, pdf_file_path)
            _LOGGER.info(f"Performing OCR for {pdf_file_path.name}")

        processed.append(
            (
                pdf_file_path,
                run_pipeline(
                    document_context=document_context,
                    steps=steps,
                ),
            )
        )

    return processed


def initialize_session_context() -> SessionContext:
    load_dotenv()
    session_context = SessionContext(
        settings=Settings.from_env(),
    )
    return initialize_mistral_client(session_context)


# -------------------- Experiment Management -------------------- #


def load_or_create_experiment(output_path: Path) -> Experiment:
    if output_path.exists():
        experiment = load_json(output_path, Experiment)
        _LOGGER.info("Existing experiment loaded.")
    else:
        experiment = Experiment(runs=[])
        _LOGGER.info("New experiment will be created.")
    return experiment


def create_run(experiment: Experiment) -> Run:
    """Create a new run with an incremented id."""
    latest_run = get_latest_run(experiment)
    new_run = Run(
        id=latest_run.id + 1 if latest_run else 1,
        date=Date.today(),
        git_hash=_get_git_hash(),
        metrics_by_file={},
    )
    experiment.runs.append(new_run)
    return new_run


def get_latest_run(experiment: Experiment) -> Run | None:
    return max(experiment.runs, key=lambda run: run.id) if experiment.runs else None


def get_run_by_id(experiment: Experiment, run_id: int) -> Run:
    run = next((run for run in experiment.runs if run.id == run_id), None)
    if run is None:
        raise ValueError(f"Run ID {run_id} not found in experiment")
    return run


def _get_git_hash() -> str:
    return git.Repo(ROOT_DIR).head.commit.hexsha


# -------------------- Experiment Workflow -------------------- #


def compute_run_summary(current_run: Run, baseline_run: Run | None) -> RunSummary:
    """Compute summary statistics for a run by comparing it to a baseline."""
    metric_summaries: dict[MetricName, MetricSummary] = {}

    # Collect all unique metric names across all files
    all_metric_names: set[MetricName] = set()
    for metric_scores in current_run.metrics_by_file.values():
        all_metric_names.update(metric_scores.keys())

    # Compute summary for each metric
    for metric_name in sorted(all_metric_names):
        deltas_by_file: dict[FileName, float | None] = {}
        regressions: list[tuple[FileName, float]] = []
        improvements: list[tuple[FileName, float]] = []
        scores: list[float] = []

        for file_name, metric_scores in current_run.metrics_by_file.items():
            if metric_name not in metric_scores:
                continue

            score = metric_scores[metric_name]
            scores.append(score)
            delta = None

            if baseline_run:
                baseline_metric_scores = baseline_run.metrics_by_file.get(file_name)
                if baseline_metric_scores and metric_name in baseline_metric_scores:
                    delta = round(score - baseline_metric_scores[metric_name], 6)
                    if delta < 0:
                        regressions.append((file_name, delta))
                    elif delta > 0:
                        improvements.append((file_name, delta))

            deltas_by_file[file_name] = delta

        # Calculate average score for this metric across all files
        average_score = sum(scores) / len(scores) if scores else 0.0

        # Sort regressions and improvements by delta
        sorted_regressions = [filename for filename, _ in sorted(regressions, key=lambda x: x[1])]
        sorted_improvements = [
            filename for filename, _ in sorted(improvements, key=lambda x: x[1], reverse=True)
        ]

        metric_summaries[metric_name] = MetricSummary(
            deltas_by_file=deltas_by_file,
            average_score=average_score,
            regressions=sorted_regressions,
            improvements=sorted_improvements,
        )

    return RunSummary(metrics=metric_summaries)


def action_generate_ground_truth(
    extract_function: ExtractFunction,
    processed_arretes: ProcessedArretes,
    ground_truth_dir: Path,
) -> None:
    """Generate ground truth data from arretify run on the PDF dataset."""
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    _LOGGER.info(f"Ground truth directory: {ground_truth_dir}")

    for pdf_file_path, document_context in processed_arretes:
        data = extract_function(document_context)
        output_json_path = ground_truth_dir / f"{pdf_file_path.stem}.json"
        dump_json(output_json_path, data)
        _LOGGER.info(f"Ground truth saved to: {output_json_path}")


def action_compute_metrics(
    extract_function: ExtractFunction,
    compute_metrics_function: ComputeMetricsFunction,
    data_model: Type[BaseModel],
    processed_arretes: ProcessedArretes,
    experiment_json_path: Path,
    ground_truth_dir: Path,
    debug_dir: Path | None,
    save_run: bool,
    compare_to_run_id: int | None = None,
) -> None:
    """Compute metrics for arretify run on the PDF dataset against ground truth."""
    _LOGGER.info(f"Ground truth directory: {ground_truth_dir}")
    _LOGGER.info(f"Experiment output path: {experiment_json_path}")

    experiment = load_or_create_experiment(experiment_json_path)
    current_run = create_run(experiment)

    # Get baseline run: use specified ID or latest run
    baseline_run: Run | None
    if compare_to_run_id is not None:
        baseline_run = get_run_by_id(experiment, compare_to_run_id)
    else:
        baseline_run = get_latest_run(experiment)

    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)
        _LOGGER.info(f"Debug directory: {debug_dir}")

    for pdf_file_path, document_context in processed_arretes:
        result_data = extract_function(document_context)
        ground_truth_data = load_json(ground_truth_dir / f"{pdf_file_path.stem}.json", data_model)

        metric_scores, debug_strings_by_metric = compute_metrics_function(
            result_data, ground_truth_data
        )

        # Store metric scores
        current_run.metrics_by_file[pdf_file_path.name] = metric_scores

        # Save debug artifacts if provided
        if debug_dir and debug_strings_by_metric:
            for metric_name, (debug_result, debug_ground_truth) in debug_strings_by_metric.items():
                ground_truth_file = (
                    debug_dir / f"{pdf_file_path.stem}.{metric_name}.ground_truth.txt"
                )
                result_file = debug_dir / f"{pdf_file_path.stem}.{metric_name}.result.txt"
                ground_truth_file.write_text(debug_ground_truth, encoding="utf-8")
                result_file.write_text(debug_result, encoding="utf-8")

    # Compute summary statistics
    summary = compute_run_summary(current_run, baseline_run)

    # Log summaries
    for metric_name, metric_summary in summary.metrics.items():
        _LOGGER.info(
            f"\n[{metric_name}] Evaluation: "
            f"{len(metric_summary.deltas_by_file)} files, avg={metric_summary.average_score:.4f}"
        )

        if baseline_run:
            _LOGGER.info(
                f"vs run {baseline_run.id}: "
                f"↓{len(metric_summary.regressions)} ↑{len(metric_summary.improvements)}"
            )

            for file_name in metric_summary.regressions:
                delta = metric_summary.deltas_by_file[file_name]
                _LOGGER.info(f"  ⚠ {file_name}: {delta:+.4f}")
            for file_name in metric_summary.improvements:
                delta = metric_summary.deltas_by_file[file_name]
                _LOGGER.info(f"  ✓ {file_name}: {delta:+.4f}")

    if save_run:
        dump_json(experiment_json_path, experiment)
        _LOGGER.info(f"Experiment saved to: {experiment_json_path}")
    else:
        _LOGGER.warning(
            "\n⚠ Run results NOT saved. To save this run to the experiment file, "
            "re-run with the --save-run flag."
        )


# -------------------- Experiment Configuration --------------------


EXPERIMENTS: dict[str, ExperimentConfig] = {
    "segmentation_in_sections": {
        "extract_function": segmentation_in_sections.build_section_tree,
        "compute_metrics_function": segmentation_in_sections.compute_metric_scores,
        "data_model": segmentation_in_sections.SectionTree,
        "default_input": ROOT_DIR / "datasets" / "quality_evaluation",
        "default_experiment_path": ROOT_DIR
        / "quality_evaluation"
        / "segmentation_in_sections.json",
        "default_ground_truth": ROOT_DIR
        / "datasets"
        / "quality_evaluation"
        / "ground_truth_segmentation_in_sections",
    },
    "tables_detection": {
        "extract_function": tables_detection.extract_tables_from_html,
        "compute_metrics_function": tables_detection.compute_metric_scores,
        "data_model": tables_detection.TablesData,
        "default_input": ROOT_DIR / "datasets" / "quality_evaluation",
        "default_experiment_path": ROOT_DIR / "quality_evaluation" / "tables_detection.json",
        "default_ground_truth": ROOT_DIR
        / "datasets"
        / "quality_evaluation"
        / "ground_truth_tables_detection",
    },
}


def main(argv: list[str] | None = None):
    """Main entry point for quality evaluation experiments."""
    if argv is None:
        argv = sys.argv

    # First parser for experiment name
    experiment_parser = argparse.ArgumentParser(
        description="Run quality evaluation experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    experiment_parser.add_argument(
        "experiment",
        choices=list(EXPERIMENTS.keys()),
        help="Which experiment to run",
    )

    if len(argv) < 2:
        experiment_parser.print_help()
        sys.exit(1)

    experiment_name = argv[1]
    if experiment_name not in EXPERIMENTS:
        experiment_parser.error(f"Invalid experiment: {experiment_name}")

    # Get experiment configuration
    config = EXPERIMENTS[experiment_name]

    # Build argument parser with actions
    parser = argparse.ArgumentParser(
        prog=f"{argv[0]} {experiment_name}",
        description=f"Run {experiment_name} experiment",
    )
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help="Input folder containing PDF files.",
    )
    parent_parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Path to cache directory for OCR results.",
    )
    parent_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (directory for generate_ground_truth, file for evaluate).",
    )

    subparsers = parser.add_subparsers(dest="action", required=True, help="Action to perform")

    subparsers.add_parser(
        "generate_ground_truth",
        parents=[parent_parser],
        help="Generate ground truth data from HTML files",
    )

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        parents=[parent_parser],
        help="Evaluate system output against ground truth",
    )
    evaluate_parser.add_argument(
        "--ground-truth",
        type=Path,
        default=None,
        help="Path to the directory containing ground truth JSON files.",
    )
    evaluate_parser.add_argument(
        "--debug-dir",
        type=Path,
        default=None,
        help=(
            "Directory where debug artifacts (intermediate representations) should be saved. "
            "To see differences in VS Code, select both files and use 'Compare Selected'."
        ),
    )
    evaluate_parser.add_argument(
        "--save-run",
        action="store_true",
        help=(
            "Save the run results to the experiment file. "
            "If not set, only displays metrics without saving."
        ),
    )
    evaluate_parser.add_argument(
        "--compare-to",
        type=int,
        default=None,
        help="Run ID to compare against. If not specified, compares to the latest run.",
    )

    # Parse remaining arguments (skip experiment name)
    args = parser.parse_args(argv[2:])

    # Apply defaults from config if not provided
    input_dir = Path(args.input) if args.input is not None else config["default_input"]

    # Validate input directory
    if not input_dir.is_dir():
        parser.error(f"Input path must be a directory: {input_dir}")

    # Create cache directory if specified
    if args.cache_dir:
        args.cache_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("arretify").setLevel(logging.ERROR)

    _LOGGER.info(f"Input directory: {input_dir}")
    if args.cache_dir:
        _LOGGER.info(f"Cache directory: {args.cache_dir}")

    # Initialize and run pipeline
    session_context = initialize_session_context()
    processed_arretes = run_arretify_on_all_pdfs(
        session_context, input_dir, ocr_cache_dir=args.cache_dir
    )

    # Execute action
    if args.action == "generate_ground_truth":
        ground_truth_dir = (
            Path(args.output) if args.output is not None else config["default_ground_truth"]
        )
        action_generate_ground_truth(
            config["extract_function"], processed_arretes, ground_truth_dir
        )
    elif args.action == "evaluate":
        experiment_json_path = (
            Path(args.output) if args.output is not None else config["default_experiment_path"]
        )
        ground_truth_dir = (
            Path(args.ground_truth)
            if args.ground_truth is not None
            else config["default_ground_truth"]
        )
        if not ground_truth_dir.is_dir():
            parser.error(f"Ground truth path must be a directory: {ground_truth_dir}")
        action_compute_metrics(
            config["extract_function"],
            config["compute_metrics_function"],
            config["data_model"],
            processed_arretes,
            experiment_json_path,
            ground_truth_dir,
            args.debug_dir if hasattr(args, "debug_dir") else None,
            args.save_run if hasattr(args, "save_run") else False,
            args.compare_to if hasattr(args, "compare_to") else None,
        )


if __name__ == "__main__":
    main()
