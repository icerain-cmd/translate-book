import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from qa_report import aggregate


class ScholarlyQAGateTests(unittest.TestCase):
    def test_not_run_required_axis_blocks_publication(self):
        report = aggregate({
            "citation_integrity": {"status": "pass"},
            "locked_terminology": {"status": "pass"},
            "epistemic_strength": {"status": "pass"},
        })
        self.assertFalse(report["publishable"])
        self.assertIn("semantic_fidelity", report["blocking_axes"])
        self.assertIn("claim_preservation", report["blocking_axes"])

    def test_all_pass_is_publishable(self):
        report = aggregate({axis: {"status": "pass"} for axis in (
            "citation_integrity", "locked_terminology", "epistemic_strength",
            "semantic_fidelity", "concept_preservation", "claim_preservation",
            "negation_preservation", "condition_preservation", "relation_preservation"
        )})
        self.assertTrue(report["publishable"])
        self.assertEqual(report["blocking_axes"], [])


if __name__ == "__main__":
    unittest.main()
