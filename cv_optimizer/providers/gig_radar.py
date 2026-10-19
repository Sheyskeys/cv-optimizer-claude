"""Read-only adapter for Gig Radar's local listing tracker."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from ..models import JobPosting


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _string_list(value: Any, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Gig Radar listing {field} must be a list")
    return tuple(text for item in value if (text := _text(item)))


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result or "listing"


def _options(values: Iterable[str] | None, defaults: tuple[str, ...], name: str) -> frozenset[str]:
    if values is None:
        return frozenset(defaults)
    if isinstance(values, str):
        raise ValueError(f"{name} must be a list of strings")
    result = frozenset(_text(value).casefold() for value in values if _text(value))
    if not result:
        raise ValueError(f"{name} must contain at least one value")
    return result


class GigRadarJsonJobProvider:
    """Import selected tracker rows without contacting job platforms.

    The tracker's fit label is retained as screening context. It is not mapped
    to required skills and is never treated as an exact-keyword match score.
    """

    def __init__(
        self,
        path: Path,
        *,
        statuses: Iterable[str] | None = None,
        fits: Iterable[str] | None = None,
        platforms: Iterable[str] | None = None,
    ):
        self.path = path
        self.statuses = _options(statuses, ("open",), "statuses")
        self.fits = _options(fits, ("strong", "possible"), "fits")
        self.platforms = (
            None if platforms is None else _options(platforms, (), "platforms")
        )

    def list_jobs(self) -> list[JobPosting]:
        with self.path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict) or not isinstance(data.get("listings"), list):
            raise ValueError(f"Expected a Gig Radar object with a listings array in {self.path}")

        scanned_at = _text(data.get("last_scan_date"))
        jobs: list[JobPosting] = []
        used_ids: set[str] = set()
        for index, row in enumerate(data["listings"]):
            if not isinstance(row, dict):
                raise ValueError(f"Gig Radar listing at index {index} must be an object")
            platform = _text(row.get("platform")) or "Unknown platform"
            title = _text(row.get("title"))
            status = _text(row.get("status")).casefold()
            fit = _text(row.get("fit")).casefold()
            if not title or status not in self.statuses or fit not in self.fits:
                continue
            if self.platforms is not None and platform.casefold() not in self.platforms:
                continue

            url = _text(row.get("url"))
            source_key = _text(row.get("id")) or url.rsplit("/", 1)[-1] or title
            job_id = f"gig-radar-{_slug(platform)}-{_slug(source_key)}"
            if job_id in used_ids:
                job_id = f"{job_id}-{index + 1}"
            used_ids.add(job_id)

            last_check = _text(row.get("last_status_check"))
            jobs.append(
                JobPosting(
                    job_id=job_id,
                    title=title,
                    company=platform,
                    description="",
                    required_skills=_string_list(row.get("required_skills"), "required_skills"),
                    preferred_skills=_string_list(row.get("preferred_skills"), "preferred_skills"),
                    source="gig-radar",
                    url=url,
                    retrieved_at=last_check or scanned_at,
                    tracking_status=status,
                    tracking_fit=fit,
                    tracking_fit_note=_text(row.get("fit_note")),
                    location_limits=_text(row.get("location_limits")),
                    pay=_text(row.get("pay")),
                    screening=_text(row.get("screening")),
                    date_first_seen=_text(row.get("date_first_seen")),
                    last_status_check=last_check,
                )
            )
        return jobs

    def get_job(self, job_id: str) -> JobPosting:
        for job in self.list_jobs():
            if job.job_id == job_id:
                return job
        raise KeyError(f"No tracked Gig Radar job with id {job_id!r} found in {self.path}")
