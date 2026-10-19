# Architecture and provider guide

The toolkit keeps source access, matching, and resume rendering separate. Core modules operate on typed records and do not import a job platform SDK.

## Data flow

```text
provider config
   ├── profile provider ──> CandidateProfile ──┐
   └── job provider ──────> JobPosting(s) ─────┼──> matching ──> ranking/report
                                                └──> resume renderer ──> Markdown draft
```

- `models.py` defines candidate, experience, and job records.
- `providers/base.py` defines the profile and job provider contracts.
- `providers/json_file.py` reads local JSON files and directories.
- `providers/stubs.py` gives explicit placeholders for future platform connectors.
- `providers/registry.py` loads configured providers and optional plugin modules.
- `matching.py` calculates exact normalized keyword coverage and lists gaps.
- `resume.py` creates a single-column draft using only supplied facts. It reorders existing skills and bullets; it does not rewrite or invent them.
- `cli.py` provides `rank` and `tailor` commands.

## Provider configuration

`config/providers.example.json` is a working example. A provider entry has a `provider` key and provider-specific settings. Relative paths are resolved from the configuration file's directory.

```json
{
  "plugins": [],
  "profile": {
    "provider": "json_file",
    "path": "../examples/candidate.example.json"
  },
  "jobs": {
    "provider": "json_file",
    "path": "../examples/jobs"
  }
}
```

A job directory contains one JSON file per posting. Each job has a stable `job_id`, title, required and preferred terms, and source metadata such as `source`, `url`, and `retrieved_at`. Record when the data was actually retrieved; do not treat an old export as current.

### Gig Radar's local tracker

`config/providers.gig-radar.example.json` reads Gig Radar's existing `seen-listings.json` through the `gig_radar_json` provider. Set `GIG_RADAR_DATA_PATH` to that file's absolute path, then run:

```bash
python3 -m cv_optimizer shortlist --config config/providers.gig-radar.example.json
```

The adapter is read-only. By default it includes tracker rows marked open and strong/possible fit, retaining their fit notes, dates, pay, screening details, URLs, and location caveats. The shortlist sorts by fit label, then newest individual status check; rows without an individual check fall below dated rows. Gig Radar's fit labels remain separate from the toolkit's exact-keyword score. Do not use `rank` to compare tracker rows unless their job descriptions and normalized skill terms have been supplied.

## Add a provider plugin

1. Create an importable Python module that adapts the source response to `CandidateProfile` or `JobPosting`.
2. Implement `get_profile()` for a profile source, and/or `list_jobs()` plus `get_job(job_id)` for a job source.
3. Register a factory from that module. Keep authentication inside the provider and read credentials from environment variables or a secrets manager.
4. Add the module's import path to the config's `plugins` list and set the provider name in `profile` or `jobs`.
5. Add tests for field mapping, missing data, pagination, stale data behavior, and authentication failures.

Example job provider skeleton:

```python
# my_project/my_jobs.py
import os
from pathlib import Path

from cv_optimizer.models import JobPosting
from cv_optimizer.providers import register_job_provider


class MyJobProvider:
    def __init__(self, spec, base_dir: Path):
        self.account = spec.get("account", "default")
        self.token = os.environ["MY_JOB_SOURCE_TOKEN"]

    def list_jobs(self) -> list[JobPosting]:
        # Fetch the source, then map each response to JobPosting.
        raise NotImplementedError("Map the source API response here")

    def get_job(self, job_id: str) -> JobPosting:
        return next(job for job in self.list_jobs() if job.job_id == job_id)


def factory(spec, base_dir):
    return MyJobProvider(spec, base_dir)


register_job_provider("my_jobs", factory)
```

Then configure it:

```json
{
  "plugins": ["my_project.my_jobs"],
  "profile": {
    "provider": "json_file",
    "path": "../examples/candidate.example.json"
  },
  "jobs": {
    "provider": "my_jobs",
    "account": "default"
  }
}
```

The plugin module must be importable in the Python environment used to run `python -m cv_optimizer`. A real connector should preserve source IDs and links, record retrieval timestamps, handle pagination/rate limits, and avoid collecting data the user is not authorized to access.

## Scoring and output limits

Matching uses normalized exact phrase coverage: required terms weigh 75% and preferred terms 25% when both are provided. If only one set exists, it determines the score. The report retains missing terms and source freshness metadata. This simple score is explainable but can miss synonyms and cannot reproduce a platform's proprietary ranking.

The Markdown renderer uses plain headings and bullets rather than tables or multi-column layouts. It ranks existing text by overlap and preserves its wording, dates, and metrics. For edits to bullet phrasing, the Claude Project should use only verified source facts and ask for missing metrics rather than inventing them.

Before making decisions, confirm job details from the live source. Platform rules change, and this repository does not automatically refresh its sample guides or listings.

## Resume guidance and evidence

The prompt and renderer favor standard section headings, a simple single-column layout, role-specific keywords only when they match the candidate's evidence, and measurable impact only when the candidate supplied a real metric. Employer instructions decide the required file type; the CLI currently outputs Markdown and does not claim one export format works for every ATS.

Recent general guidance used while shaping the workflow:

- [Indeed: How To Write an ATS-Friendly Resume](https://www.indeed.com/career-advice/resumes-cover-letters/ats-resume), updated October 6, 2026, recommends standard headings, simple formatting, truthful role-relevant keywords, and tailoring each application.
- [Indeed: Tailoring Your Resume to a Job Description](https://www.indeed.com/career-advice/resumes-cover-letters/tailoring-resume), updated August 12, 2026, discusses aligning skills to the posting and quantifying achievements where supported.

The 75/25 required/preferred weighting is a transparent starting default, not a research-validated prediction. No outcome data was supplied to calibrate it. If application outcomes are tracked later, evaluate whether the ranking helps prioritize roles and adjust the heuristic against those observed results; do not present the score as a hiring probability.
