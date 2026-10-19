"""Command-line entry point for ranking roles and rendering tailored drafts."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Sequence

from .matching import rank_jobs, score_match
from .providers import ProviderNotImplementedError, load_providers
from .resume import render_tailored_resume


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _safe_filename(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
    if not slug:
        raise ValueError("Job id cannot be converted to a safe filename")
    return slug


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default="config/providers.example.json",
        help="provider configuration JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="directory for generated files (default: %(default)s)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cv-optimizer", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    rank = commands.add_parser("rank", help="score and rank all configured job postings")
    _add_common_arguments(rank)

    tailor = commands.add_parser("tailor", help="render a role-specific resume draft")
    _add_common_arguments(tailor)
    tailor.add_argument("--job-id", required=True, help="job id from the configured provider")

    shortlist = commands.add_parser(
        "shortlist",
        help="sort tracked open roles by Gig Radar fit and status freshness",
    )
    _add_common_arguments(shortlist)
    return parser


def _shortlist_rows(jobs: list[object]) -> list[dict[str, object]]:
    def sort_key(job: object) -> tuple[int, int, int, str]:
        fit = getattr(job, "tracking_fit", "").casefold()
        fit_order = {"strong": 0, "possible": 1}.get(fit, 2)
        checked = getattr(job, "last_status_check", "")
        try:
            checked_ordinal = date.fromisoformat(str(checked)[:10]).toordinal()
        except ValueError:
            checked_ordinal = 0
        # Newer individual checks come first; undated checks follow dated ones.
        return (
            fit_order,
            0 if checked_ordinal else 1,
            -checked_ordinal,
            getattr(job, "title", "").casefold(),
        )

    ordered = sorted(jobs, key=sort_key)
    return [
        {
            "priority": index,
            "job_id": job.job_id,
            "platform": job.company,
            "title": job.title,
            "status": job.tracking_status,
            "gig_radar_fit": job.tracking_fit,
            "fit_note": job.tracking_fit_note,
            "location_limits": job.location_limits,
            "pay": job.pay,
            "screening": job.screening,
            "url": job.url,
            "first_seen": job.date_first_seen,
            "last_status_check": job.last_status_check,
            "tracker_scan_date": job.retrieved_at,
            "keyword_match_score": None,
        }
        for index, job in enumerate(ordered, start=1)
    ]


def _render_shortlist(
    rows: list[dict[str, object]], scan_date: str, candidate_context: object = None
) -> str:
    lines = [
        "# Gig Radar Shortlist",
        "",
        f"Tracker scan date: {scan_date or 'not recorded'}",
        "",
        "Sorted by Gig Radar's strong/possible fit label, then the latest available status check.",
        "Fit labels are initial screening context, not résumé keyword scores. The tracker may lag live listings; confirm each link and location terms before applying.",
        "",
    ]
    if isinstance(candidate_context, dict):
        location = candidate_context.get("location")
        authorization = candidate_context.get("work_authorization")
        if location:
            lines.append(f"Candidate location: {location}")
        if authorization:
            lines.append(f"Work-authorization note: {authorization}")
        if location or authorization:
            lines.append("")
    for fit in ("strong", "possible"):
        section = [row for row in rows if row["gig_radar_fit"] == fit]
        lines.extend((f"## {fit.title()} fit ({len(section)})", ""))
        for row in section:
            title = str(row["title"])
            url = str(row["url"])
            lines.extend(
                (
                    f"### {row['priority']}. [{row['platform']}: {title}]({url})",
                    "",
                    f"- Tracker status: {row['status']}",
                    f"- Pay shown in tracker: {row['pay'] or 'not listed'}",
                    f"- Location caveat: {row['location_limits'] or 'not recorded; verify Nigeria eligibility'}",
                    f"- Last individual status check: {row['last_status_check'] or 'not recorded'}",
                    f"- Fit note: {row['fit_note'] or 'not recorded'}",
                    f"- Screening: {row['screening'] or 'not recorded'}",
                    "",
                )
            )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile_provider, job_provider = load_providers(args.config)
        output_dir = Path(args.output_dir).expanduser()

        if args.command == "shortlist":
            jobs = job_provider.list_jobs()
            rows = _shortlist_rows(jobs)
            destination_json = output_dir / "role-shortlist.json"
            destination_md = output_dir / "role-shortlist.md"
            _write_json(destination_json, rows)
            scan_date = ""
            candidate_context = None
            provider_path = getattr(job_provider, "path", None)
            if provider_path is not None:
                with Path(provider_path).open("r", encoding="utf-8") as stream:
                    tracker = json.load(stream)
                if isinstance(tracker, dict):
                    scan_date = str(tracker.get("last_scan_date", ""))
                    candidate_context = tracker.get("candidate_context")
            destination_md.parent.mkdir(parents=True, exist_ok=True)
            destination_md.write_text(
                _render_shortlist(rows, scan_date, candidate_context), encoding="utf-8"
            )
            counts = {fit: sum(row["gig_radar_fit"] == fit for row in rows) for fit in ("strong", "possible")}
            print(f"Gig Radar shortlist: {counts['strong']} strong-fit, {counts['possible']} possible-fit roles")
            print("Confirm live status and Nigerian eligibility on each source page before applying.")
            print(f"Saved shortlist: {destination_md}")
            print(f"Saved data: {destination_json}")
            return 0

        profile = profile_provider.get_profile()

        if args.command == "rank":
            reports = rank_jobs(profile, job_provider.list_jobs())
            destination = output_dir / "role-ranking.json"
            _write_json(destination, [report.to_dict() for report in reports])
            if not reports:
                print("No job postings were found in the configured provider.")
            for position, report in enumerate(reports, start=1):
                gaps = ", ".join(report.required_missing) or "none"
                print(f"{position}. {report.score:5.1f}%  {report.title} — {report.company or 'company not listed'}")
                print(f"   Missing required terms: {gaps}")
            print(f"Saved ranking: {destination}")
            return 0

        job = job_provider.get_job(args.job_id)
        report = score_match(profile, job)
        safe_id = _safe_filename(job.job_id)
        resume_path = output_dir / f"resume-{safe_id}.md"
        report_path = output_dir / f"match-{safe_id}.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        resume_path.write_text(render_tailored_resume(profile, job), encoding="utf-8")
        _write_json(report_path, report.to_dict())
        print(f"Match coverage: {report.score:.1f}%")
        print(f"Missing required terms: {', '.join(report.required_missing) or 'none'}")
        print(f"Saved resume draft: {resume_path}")
        print(f"Saved match report: {report_path}")
        return 0
    except (
        FileNotFoundError,
        KeyError,
        ValueError,
        json.JSONDecodeError,
        ProviderNotImplementedError,
    ) as error:
        print(f"error: {error}")
        return 2
