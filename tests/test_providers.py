import json
import tempfile
import unittest
from pathlib import Path

from cv_optimizer.providers import ProviderNotImplementedError, load_providers


REPO_ROOT = Path(__file__).resolve().parents[1]


class ProviderTests(unittest.TestCase):
    def test_example_config_loads_mock_profile_and_multiple_jobs(self):
        profiles, jobs = load_providers(REPO_ROOT / "config/providers.example.json")
        self.assertEqual(profiles.get_profile().full_name, "Example Candidate")
        self.assertEqual([job.job_id for job in jobs.list_jobs()], ["app-compatibility-tester", "qa-analyst"])

    def test_stub_provider_fails_clearly_when_called(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "providers.json"
            config_path.write_text(
                json.dumps({
                    "plugins": [],
                    "profile": {"provider": "stub", "platform": "Mercor"},
                    "jobs": {"provider": "stub", "platform": "Mercor"}
                }),
                encoding="utf-8",
            )
            profiles, _ = load_providers(config_path)
            with self.assertRaisesRegex(ProviderNotImplementedError, "Mercor"):
                profiles.get_profile()

    def test_paths_resolve_relative_to_config_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "profile.json").write_text(
                json.dumps({"full_name": "Local Candidate"}), encoding="utf-8"
            )
            (root / "jobs").mkdir()
            (root / "jobs" / "job.json").write_text(
                json.dumps({"job_id": "job", "title": "Role"}), encoding="utf-8"
            )
            config = {
                "profile": {"provider": "json_file", "path": "profile.json"},
                "jobs": {"provider": "json_file", "path": "jobs"},
            }
            config_path = root / "providers.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            profiles, jobs = load_providers(config_path)
            self.assertEqual(profiles.get_profile().full_name, "Local Candidate")
            self.assertEqual(jobs.get_job("job").title, "Role")


if __name__ == "__main__":
    unittest.main()
