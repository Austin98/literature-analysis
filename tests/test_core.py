# -*- coding: utf-8 -*-
"""合成数据单元测试: 不依赖网络、不需要真实 PDF 或账号"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from clean import annotate, dedup  # noqa: E402
from import_records import parse_bib, parse_ris  # noqa: E402
from llm_tasks import merge, validate  # noqa: E402
from search import abstract_text  # noqa: E402

PROFILE = {
    "target_patterns": [r"Example Lab"],
    "contractor_patterns": [r"Example Corp"],
}


class DedupTest(unittest.TestCase):
    def test_by_doi_and_title(self):
        rows = [
            {"doi": "10.1/ABC", "title": "Same Title"},
            {"doi": "10.1/abc", "title": "Other"},
            {"doi": "", "title": "same  title!"},
            {"doi": "", "title": "Unique"},
        ]
        out = dedup(rows)
        self.assertEqual([r["title"] for r in out], ["Same Title", "Unique"])


class AnnotateTest(unittest.TestCase):
    def test_target_hit_and_funding_ignored(self):
        rows = [
            {"affiliations": [{"name": "Example Lab, Somewhere"}], "text": ""},
            {"affiliations": [{"name": "Other Univ"}],
             "text": "This work was supported by Example Lab. Authors thank nobody."},
        ]
        out = annotate(rows, PROFILE)
        self.assertTrue(out[0]["is_target"])
        self.assertFalse(out[1]["is_target"])

    def test_contractor(self):
        rows = [{"affiliations": [{"name": "Example Corp"}], "text": ""}]
        out = annotate(rows, PROFILE)
        self.assertEqual(out[0]["contractor_hits"], ["Example Corp"])
        self.assertFalse(out[0]["is_target"])


class ImportTest(unittest.TestCase):
    def test_ris(self):
        text = "TY  - JOUR\nTI  - A Test\nAU  - Li, X\nPY  - 2024\nDO  - 10.9/x\nER  -\n"
        recs = parse_ris(text)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["year"], 2024)
        self.assertEqual(recs[0]["authors"], ["Li, X"])

    def test_bib(self):
        text = '@article{k1,\n  title = {Bib Title},\n  author = {A and B},\n  year = {2023},\n}\n'
        recs = parse_bib(text)
        self.assertEqual(recs[0]["title"], "Bib Title")
        self.assertEqual(recs[0]["authors"], ["A", "B"])
        self.assertEqual(recs[0]["year"], 2023)


class SearchTest(unittest.TestCase):
    def test_abstract_rebuild(self):
        inv = {"hello": [0], "world": [1, 3], "again": [2]}
        self.assertEqual(abstract_text(inv), "hello world again world")


class LlmTasksTest(unittest.TestCase):
    def test_validate_and_merge(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out_001.jsonl"
            out.write_text(
                json.dumps({"id": "a", "doc_type": "article", "is_target": True,
                            "research_field": "T1"}, ensure_ascii=False) + "\n"
                + json.dumps({"id": "b", "doc_type": "bogus", "is_target": None,
                              "research_field": "X"}) + "\n",
                encoding="utf-8")
            errs = validate(d, expected_ids=["a", "b", "c"], topics=["T1", "T2"])
            self.assertTrue(any("doc_type" in e for e in errs))
            self.assertTrue(any("research_field" in e for e in errs))
            self.assertTrue(any("缺失" in e for e in errs))
            rows = merge([{"id": "a", "title": "x"}], d)
            self.assertEqual(rows[0]["llm_doc_type"], "article")


if __name__ == "__main__":
    unittest.main()
