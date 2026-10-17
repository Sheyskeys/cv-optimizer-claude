# AI Workers: Resume & Job Readiness Toolkit

A local-first toolkit for tailoring a resume to a specific role, comparing a candidate profile with job requirements, and preparing Claude Project guidance. It is designed to make evidence and gaps visible; it cannot guarantee interviews, platform matches, or offers.

## What is included

- `cv_optimizer/`: small Python package for profile/job records, transparent keyword matching, resume rendering, provider loading, and CLI commands
- `config/providers.example.json`: example local provider setup
- `examples/`: clearly synthetic profile and job data for trying the flow
- `tests/`: standard-library tests for core behavior
- `cv_generator_prompt.md`: Claude Project instructions for collecting and tailoring candidate information
- `mercor_profile_guide.md`: Mercor-specific working notes and official references
- `SETUP_CLAUDE.md`: instructions for setting up the Claude Project
- `docs/ARCHITECTURE.md`: module map and guide to adding providers

## Quick start

Requires Python 3.9 or newer. The core toolkit uses only the Python standard library.

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m cv_optimizer rank --config config/providers.example.json
python3 -m cv_optimizer tailor --config config/providers.example.json --job-id qa-analyst
```

The examples are synthetic. Replace them with verified candidate and job data before using the output. Commands write generated files under `output/` by default; that directory is ignored by Git.

`rank` writes `output/role-ranking.json` and prints roles in descending keyword coverage. `tailor` writes a single-column Markdown resume draft and a JSON match report. Add `--output-dir PATH` to choose another output directory.

## How matching works

The score is a transparent exact-keyword coverage heuristic. When a job contains both required and preferred terms, required coverage contributes 75% and preferred coverage 25%; if only one group is present, that group supplies the whole score. Reports include matched and missing terms, the source, URL, and retrieval date when supplied.

The 75/25 weights are a transparent starting default, not a proven predictor; no application outcome data was supplied to calibrate them. The score is not a platform's ranking formula or a prediction of hiring outcomes. It does not assess skill depth, seniority, location eligibility, work authorization, or employer preferences. Review every gap against the original resume and the live job listing. Resume format requirements vary by employer; follow each application's instructions. The guidance sources and their update dates are listed in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

The resume renderer uses simple headings and bullets, orders existing skills and bullets by keyword overlap, and preserves their wording. It does not create achievements or metrics. Use the Claude Project workflow when you want a language model to help rewrite bullets; verify every edit against the candidate's source information.

## Provider model

The included JSON providers read local candidate and job files. Explicit `stub` providers show where an external connector belongs and fail with a clear message until implemented. No job platform or profile account is contacted by this repository.

Providers implement the interfaces in `cv_optimizer/providers/base.py`. Register new providers through `cv_optimizer/providers/registry.py`; configuration selects providers by name. The configuration path is relative to the config file, so copied examples remain portable. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a walkthrough and plugin example.

For live sources, preserve the provider's source and retrieval timestamp. Check the platform's current official guidance and the job's current status before acting on imported data. Keep API credentials in environment variables or a secrets manager, never in committed configuration or sample files.

## Claude Project setup

Follow [SETUP_CLAUDE.md](SETUP_CLAUDE.md) to use the existing prompt and platform guidance in Claude Projects. The Python toolkit and Claude Project are complementary: the local CLI provides repeatable keyword coverage and formatting; the Claude Project helps reason over supplied documents. This repository does not connect to Claude or external hiring platforms automatically.

Mercor HTML snapshots are intentionally not included. Official references currently listed for the Mercor guide:

- Profile Setup: https://talent.docs.mercor.com/how-to/setup-your-profile
- Application Fit: https://talent.docs.mercor.com/announcements-and-new-releases/application-fit
- Instant Work Offers: https://talent.docs.mercor.com/new-releases/instant-offer

## Support this project

- Donation: https://donate.stripe.com/4gM28jakxeU031f2a5fAc00
- Mercor referral: https://t.mercor.com/xR1eM
- More analysis: https://mercor-insights.streamlit.app/

## License and platform relationship

See [LICENSE](LICENSE). Mercor, Micro1, Turing, and other named services are referenced for compatibility and are not owners of this repository.
