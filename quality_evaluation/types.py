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

from collections.abc import Callable
from datetime import date as Date
from pathlib import Path
from typing import Type, TypedDict, TypeVar

from pydantic import BaseModel

from arretify.types import DocumentContext

T = TypeVar("T", bound=BaseModel)

MetricName = str

FileName = str

MetricScores = dict[MetricName, float]
"""Mapping from metric name to score for a single file."""

ComputeMetricsResult = tuple[MetricScores, dict[str, tuple[str, str]] | None]
"""Return type for compute_metrics functions: (scores, debug_strings_per_metric)."""

ExtractFunction = Callable[[DocumentContext], BaseModel]
"""Type for functions that extract data from DocumentContext."""

ComputeMetricsFunction = Callable[[T, T], ComputeMetricsResult]
"""Type for functions that compute metric scores and optionally return debug strings per metric."""

# -------------------- Experiment & Run Data Structures -------------------- #


class ExperimentConfig(TypedDict):
    extract_function: ExtractFunction
    compute_metrics_function: ComputeMetricsFunction
    data_model: Type[BaseModel]
    default_input: Path
    default_experiment_path: Path
    default_ground_truth: Path


class Run(BaseModel):
    """
    Container for a single experiment run.
    """

    id: int

    date: Date

    baseline_id: int | None
    """ID of the baseline run this run compares to, if any."""

    git_hash: str

    comment: str = ""
    """Optional free-text comment for the run, empty by default (filled manually)."""

    metrics_by_file: dict[FileName, MetricScores]
    """
    Mapping from file name to metric scores.

    For example:

    {
        "file1.pdf": {
            "metric1": 0.95,
            "metric2": 1.0,
        },
        "file2.pdf": {
            "metric1": 0.87,
            "metric2": 0.92,
        },
    }
    """


class Experiment(BaseModel):
    """
    Container for multiple runs.
    """

    runs: list[Run]


# -------------------- Run summary structures -------------------- #


class MetricSummary(BaseModel):
    """Summary statistics for a single metric across all files."""

    average_score: float
    deltas_by_file: dict[FileName, float | None]
    """Delta from baseline for each file. None if no baseline or file not in baseline."""
    regressions: list[FileName]
    improvements: list[FileName]


class RunSummary(BaseModel):
    """Summary of a run's evaluation results across all files and metrics."""

    metrics: dict[MetricName, MetricSummary]
