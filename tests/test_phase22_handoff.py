import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scholarly_handoff import build, validate, markdown, resolve_artifact
from reviewer_gate import check


class Phase22Tests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.d = Path(self.t.name)
        self.s = self.d / "source.md"
        self.e = self.d / "draft-en.md"
        self.s.write_text("한국어 원문", encoding="utf-8")
        self.e.write_text("English draft", encoding="utf-8")

    def tearDown(self):
        self.t.cleanup()

    def test_valid_handoff(self):
        h = build(self.s, self.e, fresh_translation=True, translated_chunks=["chunk0001"], anchor=self.d)
        self.assertTrue(validate(h, handoff_dir=self.d)["valid"])
        self.assertIn("does **not** independently translate", markdown(h))
        self.assertEqual(h["path_policy"]["identity"], "sha256")

    def test_hash_mutation_blocks_review(self):
        h = build(self.s, self.e, anchor=self.d)
        self.e.write_text("mutated", encoding="utf-8")
        self.assertIn("translation hash mismatch", validate(h, handoff_dir=self.d)["errors"])

    def test_identical_source_translation_rejected(self):
        h = build(self.s, self.s, anchor=self.d)
        self.assertFalse(validate(h, handoff_dir=self.d)["valid"])

    def test_relative_path_survives_stale_absolute_locator(self):
        h = build(self.s, self.e, anchor=self.d)
        h["source"]["path"] = "/mnt/r/stale/source.md"
        h["translation"]["path"] = "R:\\stale\\draft-en.md"
        self.assertEqual(resolve_artifact(h["source"], self.d), self.s)
        self.assertEqual(resolve_artifact(h["translation"], self.d), self.e)
        self.assertTrue(validate(h, handoff_dir=self.d)["valid"])

    def test_schema1_backward_compatible(self):
        h = build(self.s, self.e, anchor=self.d)
        h["schema_version"] = 1
        h["source"].pop("relative_path", None); h["source"].pop("locators", None)
        h["translation"].pop("relative_path", None); h["translation"].pop("locators", None)
        self.assertTrue(validate(h, handoff_dir=self.d)["valid"])

    def test_reviewer_outputs_required(self):
        h = build(self.s, self.e, anchor=self.d)
        hp = self.d / "handoff.json"
        hp.write_text(json.dumps(h), encoding="utf-8")
        r = check(hp)
        self.assertFalse(r["valid"])
        self.assertEqual(sum(x.startswith("reviewer output missing") for x in r["errors"]), 3)

    def test_reviewer_gate_passes_with_three_outputs(self):
        h = build(self.s, self.e, anchor=self.d)
        hp = self.d / "handoff.json"
        hp.write_text(json.dumps(h), encoding="utf-8")
        f = self.d / "final.md"; a = self.d / "audit.md"; c = self.d / "changes.md"
        f.write_text("Reviewed English", encoding="utf-8")
        a.write_text("PASS", encoding="utf-8")
        c.write_text("changes", encoding="utf-8")
        self.assertTrue(check(hp, f, a, c)["valid"])


if __name__ == "__main__":
    unittest.main()
