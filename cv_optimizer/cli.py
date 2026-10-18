"""Command-line entry point for ranking roles and rendering tailored drafts."""

from __future__ import annotations

import argparse
import json
import re
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile_provider, job_provider = load_providers(args.config)
        profile = profile_provider.get_profile()
        output_dir = Path(args.output_dir).expanduser()

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
