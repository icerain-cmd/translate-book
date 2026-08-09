import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from citation_guard import protect, restore
from scholarly_preflight import build


class ScholarlyKoreanRegressionTests(unittest.TestCase):
    def test_korean_author_year_and_footnote_roundtrip(self):
        source = "이 개념은 방법론적 규율이다 (김연구, 2026). [각주: 원문 판본 확인 필요]"
        protected, mapping = protect(source)
        self.assertNotIn("김연구, 2026", protected)
        self.assertNotIn("각주:", protected)
        self.assertEqual(restore(protected, mapping), source)

    def test_repeated_citation_counts_occurrences_not_only_unique_values(self):
        source = "1. 서론\n본문 (김연구, 2026).\n5.1 하위 절\n재인용 (김연구, 2026)."
        report = build(source)
        self.assertEqual(report["protected_citation_count"], 2)
        self.assertEqual(report["unique_protected_citations"], 1)

    def test_numbered_pdf_headings_are_inferred(self):
        source = "1. 서론\n충분한 한국어 본문입니다.\n5.1 하위 절\n또 다른 한국어 본문입니다."
        report = build(source)
        self.assertEqual([h["text"] for h in report["headings"]], ["1. 서론", "5.1 하위 절"])
        self.assertEqual([h["level"] for h in report["headings"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
