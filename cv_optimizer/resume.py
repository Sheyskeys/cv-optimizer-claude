"""ATS-friendly Markdown rendering that reorders, but never invents, evidence."""

from .matching import normalize
from .models import CandidateProfile, Experience, JobPosting


def _contains_term(text: str, term: str) -> bool:
    return f" {normalize(term)} " in f" {normalize(text)} "


def _overlap_count(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if _contains_term(text, term))


def _rank_experience(role: Experience, terms: tuple[str, ...]) -> Experience:
    indexed = list(enumerate(role.bullets))
    indexed.sort(key=lambda pair: (-_overlap_count(pair[1], terms), pair[0]))
    return Experience(
        company=role.company,
        title=role.title,
        dates=role.dates,
        location=role.location,
        bullets=tuple(bullet for _, bullet in indexed),
    )


def render_tailored_resume(profile: CandidateProfile, job: JobPosting) -> str:
    """Render a simple, single-column resume using only supplied profile facts.

    Skills and existing bullets are ranked by exact keyword overlap. Wording,
    dates, employers, and metrics are preserved so tailoring cannot fabricate them.
    """
    terms = tuple(dict.fromkeys((*job.required_skills, *job.preferred_skills)))
    indexed_skills = list(enumerate(profile.skills))
    indexed_skills.sort(key=lambda pair: (-_overlap_count(pair[1], terms), pair[0]))
    ranked_skills = [skill for _, skill in indexed_skills]

    lines = [f"# {profile.full_name}"]
    if profile.headline:
        lines.extend(("", profile.headline))
    if profile.contact:
        lines.extend(("", " | ".join(profile.contact)))
    lines.extend(("", f"Target role: {job.title}" + (f" at {job.company}" if job.company else "")))

    if profile.summary:
        lines.extend(("", "## Professional Summary", "", profile.summary))
    if ranked_skills:
        lines.extend(("", "## Skills & Tools", "", " | ".join(ranked_skills)))
    if profile.experience:
        lines.extend(("", "## Professional Experience"))
        for original in profile.experience:
            role = _rank_experience(original, terms)
            heading = f"### {role.title} — {role.company}"
            lines.extend(("", heading))
            if role.dates or role.location:
                detail = " | ".join(part for part in (role.dates, role.location) if part)
                lines.extend((detail,))
            lines.extend(f"- {bullet}" for bullet in role.bullets)
    if profile.education:
        lines.extend(("", "## Education", ""))
        lines.extend(f"- {item}" for item in profile.education)
    return "\n".join(lines).rstrip() + "\n"
