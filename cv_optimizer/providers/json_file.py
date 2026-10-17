"""Local JSON providers suitable for manual exports and mocked examples."""

import json
from pathlib import Path
from typing import Any

from ..models import CandidateProfile, JobPosting


def _read_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return data


class JsonFileProfileProvider:
    def __init__(self, path: Path):
        self.path = path

    def get_profile(self) -> CandidateProfile:
        return CandidateProfile.from_dict(_read_object(self.path))


class JsonFileJobProvider:
    def __init__(self, path: Path):
        self.path = path

    def list_jobs(self) -> list[JobPosting]:
        paths = sorted(self.path.glob("*.json")) if self.path.is_dir() else [self.path]
        return [JobPosting.from_dict(_read_object(path)) for path in paths]

    def get_job(self, job_id: str) -> JobPosting:
        for job in self.list_jobs():
            if job.job_id == job_id:
                return job
        raise KeyError(f"No job with id {job_id!r} found in {self.path}")
