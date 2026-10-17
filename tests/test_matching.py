import unittest

from cv_optimizer.matching import rank_jobs, score_match
from cv_optimizer.models import CandidateProfile, Experience, JobPosting


class ScoreMatchTests(unittest.TestCase):
    def setUp(self):
        self.profile = CandidateProfile(
            full_name="Test Candidate",
            skills=("Web testing", "Bug reporting", "Regression testing"),
            experience=(Experience("Example Co", "Tester", bullets=("Performed web testing.",)),),
        )

    def test_weights_required_terms_more_than_preferred_terms(self):
        job = JobPosting(
            job_id="qa",
            title="QA Analyst",
            required_skills=("web testing", "API testing"),
            preferred_skills=("regression testing",),
        )
        report = score_match(self.profile, job)
        self.assertEqual(report.score, 62.5)
        self.assertEqual(report.required_matched, ("web testing",))
        self.assertEqual(report.required_missing, ("API testing",))
        self.assertEqual(report.preferred_matched, ("regression testing",))

    def test_punctuation_and_case_are_normalized(self):
        job = JobPosting(job_id="qa", title="QA", required_skills=("BUG-REPORTING",))
        self.assertEqual(score_match(self.profile, job).score, 100.0)

    def test_preferred_terms_are_used_when_no_required_terms_exist(self):
        job = JobPosting(job_id="qa", title="QA", preferred_skills=("web testing", "API testing"))
        report = score_match(self.profile, job)
        self.assertEqual(report.score, 50.0)
        self.assertEqual(report.preferred_missing, ("API testing",))

    def test_report_labels_heuristic_and_source_freshness(self):
        job = JobPosting(
            job_id="qa", title="QA", source="manual-export", retrieved_at="2026-10-17"
        )
        report = score_match(self.profile, job).to_dict()
        self.assertEqual(report["source"], "manual-export")
        self.assertEqual(report["retrieved_at"], "2026-10-17")
        self.assertIn("not a platform score", report["scoring_note"])

    def test_rank_jobs_sorts_by_score_then_job_id(self):
        lower = JobPosting(job_id="z-lower", title="Lower", required_skills=("API testing",))
        higher = JobPosting(job_id="a-higher", title="Higher", required_skills=("web testing",))
        same_score_earlier_id = JobPosting(job_id="a-tie", title="Tie", required_skills=("web testing",))
        reports = rank_jobs(self.profile, (lower, higher, same_score_earlier_id))
        self.assertEqual([report.job_id for report in reports], ["a-higher", "a-tie", "z-lower"])


if __name__ == "__main__":
    unittest.main()
