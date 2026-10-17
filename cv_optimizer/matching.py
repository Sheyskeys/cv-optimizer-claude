"""Transparent keyword-coverage matching; this is not an employer's score."""

import re
from dataclasses import asdict, dataclass
from typing import Iterable

from .models import CandidateProfile, JobPosting


def normalize(text: str) -> str:
    """Normalize punctuation and case while retaining word boundaries."""
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = normalize(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value.strip())
    return tuple(result)


def candidate_evidence(profile: CandidateProfile) -> str:
    parts = [profile.headline, profile.summary, *profile.skills]
    for role in profile.experience:
        parts.extend((role.title, role.company, *role.bullets))
    parts.extend(profile.education)
    return normalize(" ".join(parts))


def _matched_terms(terms: Iterable[str], evidence: str) -> tuple[str, ...]:
    normalized_evidence = f" {evidence} "
    return tuple(
        term for term in _unique(terms)
        if f" {normalize(term)} " in normalized_evidence
    )


@dataclass(frozen=True)
class MatchReport:
    job_id: str
    title: str
    company: str
    source: str
    url: str
    retrieved_at: str
    score: float
    required_matched: tuple[str, ...]
    required_missing: tuple[str, ...]
    preferred_matched: tuple[str, ...]
    preferred_missing: tuple[str, ...]
    scoring_note: str = (
        "Exact normalized keyword coverage only; this is not a platform score "
        "or a prediction of hiring outcomes."
    )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def score_match(profile: CandidateProfile, job: JobPosting) -> MatchReport:
    required = _unique(job.required_skills)
    preferred = _unique(job.preferred_skills)
    evidence = candidate_evidence(profile)
    required_matched = _matched_terms(required, evidence)
    preferred_matched = _matched_terms(preferred, evidence)
    required_missing = tuple(term for term in required if term not in required_matched)
    preferred_missing = tuple(term for term in preferred if term not in preferred_matched)

    required_coverage = len(required_matched) / len(required) if required else None
    preferred_coverage = len(preferred_matched) / len(preferred) if preferred else None
    if required_coverage is not None and preferred_coverage is not None:
        score = 100 * (0.75 * required_coverage + 0.25 * preferred_coverage)
    elif required_coverage is not None:
        score = 100 * required_coverage
    elif preferred_coverage is not None:
        score = 100 * preferred_coverage
    else:
        score = 0.0

    return MatchReport(
        job_id=job.job_id,
        title=job.title,
        company=job.company,
        source=job.source,
        url=job.url,
        retrieved_at=job.retrieved_at,
        score=round(score, 1),
        required_matched=required_matched,
        required_missing=required_missing,
        preferred_matched=preferred_matched,
        preferred_missing=preferred_missing,
    )


def rank_jobs(profile: CandidateProfile, jobs: Iterable[JobPosting]) -> list[MatchReport]:
    """Return deterministic role rankings by score, then job id."""
    reports = [score_match(profile, job) for job in jobs]
    reports.sort(key=lambda report: (-report.score, report.job_id))
    return reports
