import unittest

from cv_optimizer.models import CandidateProfile, Experience, JobPosting
from cv_optimizer.resume import render_tailored_resume


class TailoredResumeTests(unittest.TestCase):
    def test_reorders_existing_evidence_without_rewriting_it(self):
        original_bullets = (
            "Prepared weekly team notes.",
            "Reported web testing defects with reproducible steps.",
        )
        profile = CandidateProfile(
            full_name="Test Candidate",
            skills=("Team notes", "Web testing", "Bug reporting"),
            experience=(Experience("Example Co", "Tester", bullets=original_bullets),),
        )
        job = JobPosting(
            job_id="qa", title="QA Analyst", required_skills=("web testing", "bug reporting")
        )
        rendered = render_tailored_resume(profile, job)
        self.assertLess(rendered.index("Web testing"), rendered.index("Team notes"))
        self.assertLess(
            rendered.index("Reported web testing defects"),
            rendered.index("Prepared weekly team notes"),
        )
        self.assertIn("Reported web testing defects with reproducible steps.", rendered)
        self.assertNotIn("100%", rendered)

    def test_uses_single_column_plain_markdown_sections(self):
        profile = CandidateProfile(full_name="Test Candidate", summary="Verified summary.")
        job = JobPosting(job_id="qa", title="QA Analyst")
        rendered = render_tailored_resume(profile, job)
        self.assertIn("## Professional Summary", rendered)
        self.assertNotIn("|---", rendered)
        self.assertTrue(rendered.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
