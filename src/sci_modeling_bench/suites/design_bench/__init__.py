"""Modernized datasets derived from Design-Bench."""

from sci_modeling_bench.suites.design_bench.black_box_optimization import (
    BlackBoxOptimizationEvaluation,
    CandidateEvaluation,
    CandidateValidationReport,
    CandidateViolation,
    DesignBenchBlackBoxOptimizationTask,
)
from sci_modeling_bench.suites.design_bench.tfbind8 import (
    DEFAULT_TFBIND8_SOURCE,
    TFBIND8_CONFIG_NAME,
    TFBIND8_DEFAULT_SPLIT,
    TFBind8BlackBoxOptimizationTask,
    TFBind8Dataset,
    TFBind8DesignBenchProtocol,
    TFBind8ExactObjective,
    TFBind8Validator,
)

__all__ = [
    "BlackBoxOptimizationEvaluation",
    "CandidateEvaluation",
    "CandidateValidationReport",
    "CandidateViolation",
    "DEFAULT_TFBIND8_SOURCE",
    "DesignBenchBlackBoxOptimizationTask",
    "TFBIND8_CONFIG_NAME",
    "TFBIND8_DEFAULT_SPLIT",
    "TFBind8Dataset",
    "TFBind8BlackBoxOptimizationTask",
    "TFBind8DesignBenchProtocol",
    "TFBind8ExactObjective",
    "TFBind8Validator",
]
