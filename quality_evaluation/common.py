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
"""Common utilities for quality evaluation measurements."""

import argparse
import logging
from datetime import date as Date
from pathlib import Path
from typing import Type, TypeVar

import git
from dotenv import load_dotenv
from pydantic import BaseModel

from arretify.law_data.apis.mistral import initialize_mistral_client
from arretify.pipeline import load_ocr_pages, load_pdf_file, run_pipeline
from arretify.settings import Settings
from arretify.step_markdown_cleaning import step_markdown_cleaning
from arretify.step_ocr import step_ocr
from arretify.step_segmentation import step_segmentation
from arretify.types import DocumentContext, SessionContext

_LOGGER = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).parent.parent

# -------------------- Data Models -------------------- #


class Evaluation(BaseModel):
    """
    Container for evaluation results of a single file, including the computed value
    and delta from baseline.
    """

    file_name: str
    value: float
    delta: float | None


class Run(BaseModel):
    """
    Container for a single evaluation run.
    """

    date: Date

    baseline_date: Date | None
    """Date of the baseline run this run compares to, if any."""

    git_hash: str

    evaluation_sets: dict[str, dict[str, Evaluation]]
    """
    Mapping from metric name to a mapping of file name to Evaluation.

    For example:

    {
        "metric1": {
            "file1.pdf": Evaluation(...),
            "file2.pdf": Evaluation(...),
        },
        "metric2": {
            "file1.pdf": Evaluation(...),
            "file2.pdf": Evaluation(...),
        },
    }
    """


class Experiment(BaseModel):
    """
    Container for multiple evaluation runs.
    """

    runs: list[Run]


# -------------------- JSON I/O -------------------- #

T = TypeVar("T", bound=BaseModel)


def dump_json(output_json_path: Path, model: BaseModel) -> None:
    output_json_path.write_text(model.model_dump_json(indent=2), encoding="utf-8")


def load_json(json_path: Path, model_class: Type[T]) -> T:
    try:
        return model_class.model_validate_json(json_path.read_text(encoding="utf-8"))
    except Exception:
        _LOGGER.error(f"Error loading JSON from {json_path}")
        raise


# -------------------- PDF processing -------------------- #


def convert_pdf_to_html(
    session_context: SessionContext, pdf_file_path: Path, cache_dir: Path | None
) -> DocumentContext:
    """
    Convert PDF to HTML, using cache if available.
    """
    ocr_pages_dir = None
    if cache_dir is not None:
        ocr_pages_dir = cache_dir / pdf_file_path.stem

    # If cache directory for OCR pages exists, load from cache and skip OCR step.
    if ocr_pages_dir and ocr_pages_dir.exists():
        if not ocr_pages_dir.is_dir():
            raise ValueError(f"Cache path {ocr_pages_dir} exists and is not a directory.")
        _LOGGER.info(f"Loading OCR pages from cache directory for {pdf_file_path.name}")
        return run_pipeline(
            load_ocr_pages(session_context, ocr_pages_dir),
            [step_markdown_cleaning, step_segmentation],
        )

    # Else perform OCR and optionally save to cache if cache directory is provided.
    else:
        if ocr_pages_dir is not None:
            ocr_pages_dir.mkdir(parents=True, exist_ok=True)

        def step_ocr_with_cache(
            document_context: DocumentContext,
        ) -> DocumentContext:
            return step_ocr(
                document_context=document_context,
                ocr_pages_dir=ocr_pages_dir,
            )

        _LOGGER.info(f"Performing OCR for {pdf_file_path.name}")
        return run_pipeline(
            load_pdf_file(session_context, pdf_file_path),
            [step_ocr_with_cache, step_markdown_cleaning, step_segmentation],
        )


def load_all_pdfs(
    session_context: SessionContext, input_dir: Path, cache_dir: Path | None
) -> list[tuple[Path, DocumentContext]]:
    """
    Load all PDFs from input directory, processing or using cache as needed.
    """
    pdf_file_paths: list[Path] = []
    for entry in input_dir.iterdir():
        if entry.is_file() and entry.suffix.lower() == ".pdf":
            pdf_file_paths.append(entry)
    loaded: list[tuple[Path, DocumentContext]] = []
    for pdf_file_path in sorted(pdf_file_paths):
        loaded.append(
            (
                pdf_file_path,
                convert_pdf_to_html(session_context, pdf_file_path, cache_dir=cache_dir),
            )
        )
    return loaded


# -------------------- Experiment Management -------------------- #


def initialize_session_context() -> SessionContext:
    load_dotenv()
    session_context = SessionContext(
        settings=Settings.from_env(),
    )
    return initialize_mistral_client(session_context)


def load_or_create_experiment(output_path: Path) -> Experiment:
    if output_path.exists():
        experiment = load_json(output_path, Experiment)
        _LOGGER.info("Existing experiment loaded.")
    else:
        experiment = Experiment(runs=[])
        _LOGGER.info("New experiment will be created.")
    return experiment


def prepare_current_run(experiment: Experiment) -> tuple[Run, Run | None]:
    """Prepare a new run for today, removing any existing run for today."""
    if any(run.date == Date.today() for run in experiment.runs):
        _LOGGER.info("Removing existing run for today.")
        experiment.runs = [run for run in experiment.runs if run.date != Date.today()]

    baseline_run = experiment.runs[-1] if experiment.runs else None
    current_run = Run(
        date=Date.today(),
        baseline_date=baseline_run.date if baseline_run else None,
        git_hash=_get_git_hash(),
        evaluation_sets={},
    )
    experiment.runs.append(current_run)
    return (current_run, baseline_run)


def log_evaluation_summary(current_run: Run, baseline_run: Run | None, metric_name: str) -> None:
    """Log evaluation summary with comparison to baseline if available."""
    evaluations = current_run.evaluation_sets.get(metric_name, {})
    if not evaluations:
        _LOGGER.warning(f"No evaluations found for metric '{metric_name}'")
        return

    total = len(evaluations)
    avg_score = sum(e.value for e in evaluations.values()) / total
    _LOGGER.info(f"\n[{metric_name}] Evaluation: {total} files, avg={avg_score:.4f}")

    if baseline_run:
        regressions: list[Evaluation] = [
            e for e in evaluations.values() if e.delta is not None and e.delta < 0
        ]
        improvements: list[Evaluation] = [
            e for e in evaluations.values() if e.delta is not None and e.delta > 0
        ]
        _LOGGER.info(f"vs {baseline_run.date}: ↓{len(regressions)} ↑{len(improvements)}")

        if regressions:
            for e in sorted(regressions, key=lambda x: x.delta):
                _LOGGER.info(f"  ⚠ {e.file_name}: {e.delta:+.4f}")
        if improvements:
            for e in sorted(improvements, key=lambda x: x.delta, reverse=True):
                _LOGGER.info(f"  ✓ {e.file_name}: {e.delta:+.4f}")


def create_evaluation_with_delta(
    file_name: str,
    value: float,
    baseline_run: Run | None,
    metric_name: str,
) -> Evaluation:
    """
    Create an Evaluation with delta computed from baseline run.

    Args:
        file_name: Name of the file being evaluated
        value: The computed metric value for this evaluation
        baseline_run: Previous run to compare against (or None)
        metric_name: Name of the metric (e.g., 'segmentation', 'tables')
    """
    baseline_evaluation = None
    if baseline_run:
        baseline_evaluations = baseline_run.evaluation_sets.get(metric_name, {})
        baseline_evaluation = baseline_evaluations.get(file_name)
        if baseline_evaluation is None:
            _LOGGER.debug(
                f"No baseline evaluation found for {file_name} " f"in run dated {baseline_run.date}"
            )

    return Evaluation(
        file_name=file_name,
        value=value,
        delta=(value - baseline_evaluation.value if baseline_evaluation is not None else None),
    )


def _get_git_hash() -> str:
    return git.Repo(ROOT_DIR).head.commit.hexsha


# -------------------- Argument Parsing -------------------- #


def create_base_parser(
    default_input: Path | None = None, default_output: Path | None = None
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-i",
        "--input",
        default=default_input,
        help="Input folder containing PDF files.",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Path to cache directory for OCR results.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=default_output,
        help="Output JSON file path for experiment results.",
    )
    return parser


def add_evaluation_arguments(
    parser: argparse.ArgumentParser, default_ground_truth: Path | None = None
) -> None:
    """Add common evaluation arguments to parser."""
    parser.add_argument(
        "--ground-truth",
        default=default_ground_truth,
        help="Path to the directory containing ground truth JSON files.",
    )
    parser.add_argument(
        "--diff-dir",
        default=None,
        help=(
            "Directory where diff files should be saved. To see differences in VS Code, "
            "select both files and use 'Compare Selected'."
        ),
    )
