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
import tempfile
import unittest
from datetime import date as Date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from quality_evaluation.main import compute_run_summary, load_json, main
from quality_evaluation.types import Experiment, Run


class TestMain(unittest.TestCase):
    def test_main_evaluate_tables_detection_creates_experiment(self):
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_dir = temp_path / "input"
            input_dir.mkdir()
            ground_truth_dir = temp_path / "ground_truth"
            ground_truth_dir.mkdir()
            experiment_json_path = temp_path / "experiment.json"

            # Create test PDF file
            test_pdf = input_dir / "test.pdf"
            test_pdf.write_bytes(b"%PDF-1.4 fake pdf")

            # Create ground truth
            ground_truth_file = ground_truth_dir / "test.json"
            ground_truth_file.write_text(
                '{"tables_by_page": {"2": ["<table><tr><td>Ground Truth</td></tr></table>"]}}',
                encoding="utf-8",
            )

            # Mock pipeline functions
            mock_session_context = MagicMock()
            mock_document_context = MagicMock()
            mock_soup = BeautifulSoup(
                (
                    "<html><body>"
                    '<a data-spec="page_separator" data-page_index="1"></a>'
                    "<table><tr><td>Ground Truth</td></tr></table>"
                    "</body></html>"
                ),
                "html.parser",
            )
            mock_document_context.soup = mock_soup

            with (
                patch(
                    "quality_evaluation.main.initialize_session_context",
                    return_value=mock_session_context,
                ),
                patch(
                    "quality_evaluation.main.run_arretify_on_all_pdfs",
                    return_value=[(test_pdf, mock_document_context)],
                ),
                patch("quality_evaluation.main._get_git_hash", return_value="test123"),
            ):
                # Act
                main(
                    [
                        "main.py",
                        "tables_detection",
                        "evaluate",
                        "--input",
                        str(input_dir),
                        "--ground-truth",
                        str(ground_truth_dir),
                        "--output",
                        str(experiment_json_path),
                    ]
                )

            # Assert
            assert experiment_json_path.exists()
            experiment = load_json(experiment_json_path, Experiment)

            expected_run = Run(
                id=1,
                date=Date.today(),
                baseline_id=None,
                git_hash="test123",
                metrics_by_file={
                    "test.pdf": {
                        "recall": 1.0,
                        "precision": 1.0,
                        "structure_accuracy": 1.0,
                        "general_accuracy": 1.0,
                    }
                },
            )

            assert experiment.runs == [expected_run]


class TestComputeRunSummary(unittest.TestCase):

    def test_compute_run_summary_without_baseline(self):
        # Arrange
        current_run = Run(
            id=1,
            date=Date.today(),
            baseline_id=None,
            git_hash="abc123",
            metrics_by_file={
                "file1.pdf": {"recall": 0.95, "precision": 0.90},
                "file2.pdf": {"recall": 0.85, "precision": 0.88},
            },
        )

        # Act
        summary = compute_run_summary(current_run, baseline_run=None)

        # Assert
        assert set(summary.metrics.keys()) == {"precision", "recall"}

        # Check precision metric
        precision_summary = summary.metrics["precision"]
        assert precision_summary.average_score == pytest.approx(0.89)
        assert precision_summary.deltas_by_file == {
            "file1.pdf": None,
            "file2.pdf": None,
        }
        assert precision_summary.regressions == []
        assert precision_summary.improvements == []

        # Check recall metric
        recall_summary = summary.metrics["recall"]
        assert recall_summary.average_score == pytest.approx(0.90)
        assert recall_summary.deltas_by_file == {
            "file1.pdf": None,
            "file2.pdf": None,
        }
        assert recall_summary.regressions == []
        assert recall_summary.improvements == []

    def test_compute_run_summary_with_baseline(self):
        # Arrange
        baseline_run = Run(
            id=1,
            date=Date.today(),
            baseline_id=None,
            git_hash="baseline123",
            metrics_by_file={
                "file1.pdf": {"recall": 0.90, "precision": 0.85},
                "file2.pdf": {"recall": 0.80, "precision": 0.90},
                "file3.pdf": {"recall": 0.75, "precision": 0.80},
            },
        )

        current_run = Run(
            id=2,
            date=Date.today(),
            baseline_id=1,
            git_hash="current456",
            metrics_by_file={
                "file1.pdf": {"recall": 0.95, "precision": 0.80},  # recall +0.05, precision -0.05
                "file2.pdf": {"recall": 0.75, "precision": 0.95},  # recall -0.05, precision +0.05
                "file3.pdf": {"recall": 0.75, "precision": 0.80},  # no change
            },
        )

        # Act
        summary = compute_run_summary(current_run, baseline_run=baseline_run)

        # Assert
        assert set(summary.metrics.keys()) == {"precision", "recall"}

        # Check precision metric
        precision_summary = summary.metrics["precision"]
        assert precision_summary.average_score == pytest.approx(0.85)
        assert precision_summary.deltas_by_file["file1.pdf"] == pytest.approx(-0.05)
        assert precision_summary.deltas_by_file["file2.pdf"] == pytest.approx(0.05)
        assert precision_summary.deltas_by_file["file3.pdf"] == pytest.approx(0.0)
        assert precision_summary.regressions == ["file1.pdf"]
        assert precision_summary.improvements == ["file2.pdf"]

        # Check recall metric
        recall_summary = summary.metrics["recall"]
        assert recall_summary.average_score == pytest.approx(0.8166666666666667)
        assert recall_summary.deltas_by_file["file1.pdf"] == pytest.approx(0.05)
        assert recall_summary.deltas_by_file["file2.pdf"] == pytest.approx(-0.05)
        assert recall_summary.deltas_by_file["file3.pdf"] == pytest.approx(0.0)
        assert recall_summary.regressions == ["file2.pdf"]
        assert recall_summary.improvements == ["file1.pdf"]


if __name__ == "__main__":
    unittest.main()
