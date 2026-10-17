"""Typed records shared by providers, matching, and resume rendering."""

from dataclasses import dataclass
from typing import Any, Mapping


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _text_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("Expected a list of strings")
    return tuple(text for item in value if (text := _text(item)))


@dataclass(frozen=True)
class Experience:
    company: str
    title: str
    dates: str = ""
    location: str = ""
    bullets: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Experience":
        company = _text(data.get("company"))
        title = _text(data.get("title"))
        if not company or not title:
            raise ValueError("Each experience entry needs company and title")
        return cls(
            company=company,
            title=title,
            dates=_text(data.get("dates")),
            location=_text(data.get("location")),
            bullets=_text_list(data.get("bullets", [])),
        )


@dataclass(frozen=True)
class CandidateProfile:
    full_name: str
    headline: str = ""
    summary: str = ""
    contact: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()
    experience: tuple[Experience, ...] = ()
    education: tuple[str, ...] = ()
    source: str = "local-json"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CandidateProfile":
        full_name = _text(data.get("full_name"))
        if not full_name:
            raise ValueError("Candidate profile needs full_name")
        raw_experience = data.get("experience", [])
        if not isinstance(raw_experience, list):
            raise ValueError("experience must be a list")
        if not all(isinstance(item, Mapping) for item in raw_experience):
            raise ValueError("each experience entry must be an object")
        return cls(
            full_name=full_name,
            headline=_text(data.get("headline")),
            summary=_text(data.get("summary")),
            contact=_text_list(data.get("contact", [])),
            skills=_text_list(data.get("skills", [])),
            experience=tuple(Experience.from_dict(item) for item in raw_experience),
            education=_text_list(data.get("education", [])),
            source=_text(data.get("source")) or "local-json",
        )


@dataclass(frozen=True)
class JobPosting:
    job_id: str
    title: str
    company: str = ""
    description: str = ""
    required_skills: tuple[str, ...] = ()
    preferred_skills: tuple[str, ...] = ()
    source: str = "local-json"
    url: str = ""
    retrieved_at: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "JobPosting":
        job_id = _text(data.get("job_id"))
        title = _text(data.get("title"))
        if not job_id or not title:
            raise ValueError("Job posting needs job_id and title")
        return cls(
            job_id=job_id,
            title=title,
            company=_text(data.get("company")),
            description=_text(data.get("description")),
            required_skills=_text_list(data.get("required_skills", [])),
            preferred_skills=_text_list(data.get("preferred_skills", [])),
            source=_text(data.get("source")) or "local-json",
            url=_text(data.get("url")),
            retrieved_at=_text(data.get("retrieved_at")),
        )
