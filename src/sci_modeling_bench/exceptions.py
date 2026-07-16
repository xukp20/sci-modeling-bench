"""Package-specific exceptions."""


class SciModelingBenchError(Exception):
    """Base exception for package failures."""


class ManifestError(SciModelingBenchError):
    """Raised when a dataset manifest is missing or invalid."""


class DatasetLoadError(SciModelingBenchError):
    """Raised when dataset resources cannot be resolved or loaded."""


class SchemaMismatchError(SciModelingBenchError):
    """Raised when published data does not match its manifest schema."""


class ObjectiveError(SciModelingBenchError):
    """Base exception for Objective construction and evaluation failures."""


class ObjectiveInputError(ObjectiveError):
    """Raised when a candidate fails the bound Dataset input contract."""

    def __init__(self, candidate_index: int, report: object) -> None:
        self.candidate_index = candidate_index
        self.report = report
        super().__init__(
            f"candidate at batch index {candidate_index} is invalid for the "
            "bound Dataset"
        )


class ObjectiveLookupError(ObjectiveError):
    """Raised when a valid candidate is absent from an exact lookup artifact."""


class ObjectiveOutputError(ObjectiveError):
    """Raised when an Objective violates its declared output contract."""


class ProtocolError(SciModelingBenchError):
    """Raised when a Protocol cannot build its declared Agent input."""


class TaskError(SciModelingBenchError):
    """Raised when a Task definition or trusted evaluation is inconsistent."""
