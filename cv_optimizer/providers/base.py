"""Provider contracts for candidate profiles and job listings."""

from pathlib import Path
from typing import Protocol

from ..models import CandidateProfile, JobPosting


class ProviderNotImplementedError(RuntimeError):
    """Raised when an example provider has not been connected yet."""


class ProfileProvider(Protocol):
    def get_profile(self) -> CandidateProfile: ...


class JobProvider(Protocol):
    def list_jobs(self) -> list[JobPosting]: ...

    def get_job(self, job_id: str) -> JobPosting: ...


class ProviderFactory(Protocol):
    def __call__(self, spec: dict[str, object], base_dir: Path) -> object: ...
