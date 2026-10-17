"""Explicit placeholders for future platform-specific connectors."""

from pathlib import Path

from .base import ProviderNotImplementedError


class StubProfileProvider:
    def __init__(self, spec: dict[str, object], base_dir: Path):
        self.platform = str(spec.get("platform", "external profile source"))

    def get_profile(self):
        raise ProviderNotImplementedError(
            f"{self.platform} profile provider is a stub; implement authentication "
            "and mapping before using it."
        )


class StubJobProvider:
    def __init__(self, spec: dict[str, object], base_dir: Path):
        self.platform = str(spec.get("platform", "external job source"))

    def list_jobs(self):
        raise ProviderNotImplementedError(
            f"{self.platform} job provider is a stub; implement authentication "
            "and mapping before using it."
        )

    def get_job(self, job_id: str):
        raise ProviderNotImplementedError(
            f"{self.platform} job provider is a stub; implement authentication "
            "and mapping before using it."
        )
