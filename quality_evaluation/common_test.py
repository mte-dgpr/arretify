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
import unittest
from datetime import date as Date
from unittest.mock import patch

from quality_evaluation.common import (
    Evaluation,
    Experiment,
    Run,
    create_evaluation_with_delta,
    prepare_current_run,
)


class TestCreateEvaluationWithDelta(unittest.TestCase):
    def test_create_evaluation_without_baseline(self):
        # Arrange
        file_name = "test.pdf"
        value = 0.85
        baseline_run = None
        metric_name = "segmentation"

        # Act
        evaluation = create_evaluation_with_delta(file_name, value, baseline_run, metric_name)

        # Assert
        assert evaluation.file_name == "test.pdf"
        assert evaluation.value == 0.85
        assert evaluation.delta is None

    def test_create_evaluation_with_baseline(self):
        # Arrange
        baseline_run = Run(
            date=Date(2026, 2, 1),
            baseline_date=None,
            git_hash="abc123",
            evaluation_sets={
                "segmentation": {
                    "test.pdf": Evaluation(file_name="test.pdf", value=0.80, delta=None)
                }
            },
        )
        file_name = "test.pdf"
        value = 0.85
        metric_name = "segmentation"

        # Act
        evaluation = create_evaluation_with_delta(file_name, value, baseline_run, metric_name)

        # Assert
        assert evaluation.file_name == "test.pdf"
        assert evaluation.value == 0.85
        assert abs(evaluation.delta - 0.05) < 1e-5


class TestPrepareCurrentRun(unittest.TestCase):
    @patch("quality_evaluation.common.get_git_hash")
    @patch("quality_evaluation.common.Date")
    def test_prepare_current_run_with_no_existing_runs(self, mock_date, mock_git_hash):
        # Arrange
        mock_date.today.return_value = Date(2026, 2, 4)
        mock_git_hash.return_value = "xyz789"
        experiment = Experiment(runs=[])

        # Act
        current_run, baseline_run = prepare_current_run(experiment)

        # Assert
        assert current_run.date == Date(2026, 2, 4)
        assert current_run.baseline_date is None
        assert current_run.git_hash == "xyz789"
        assert current_run.evaluation_sets == {}
        assert len(experiment.runs) == 1
        assert baseline_run is None

    @patch("quality_evaluation.common.get_git_hash")
    @patch("quality_evaluation.common.Date")
    def test_prepare_current_run_with_existing_runs(self, mock_date, mock_git_hash):
        # Arrange
        mock_date.today.return_value = Date(2026, 2, 4)
        mock_git_hash.return_value = "xyz789"
        run1 = Run(date=Date(2026, 2, 1), baseline_date=None, git_hash="abc", evaluation_sets={})
        experiment = Experiment(runs=[run1])

        # Act
        current_run, baseline_run = prepare_current_run(experiment)

        # Assert
        assert current_run.date == Date(2026, 2, 4)
        assert current_run.baseline_date == Date(2026, 2, 1)
        assert current_run.git_hash == "xyz789"
        assert len(experiment.runs) == 2
        assert baseline_run == run1
