import unittest

from analyze_baseline import analyze, member_present


class BaselineTests(unittest.TestCase):
    def test_archive_contract_matching(self):
        self.assertTrue(member_present("report.md|report.pdf", ["report.pdf"]))
        self.assertTrue(member_present("specs/", ["specs/26.docx"]))
        self.assertFalse(member_present("report.md", []))
        self.assertFalse(member_present("report.md", ["extra/report.md"]))

    def test_inherited_manifest_coverage_and_provenance(self):
        manifest, rows = analyze()
        self.assertEqual(len(rows), 29)
        self.assertEqual({row["task"] for row in rows}, set(manifest["tasks"]))
        self.assertTrue(all(row["config"] == "baseline (template)" for row in rows))
        self.assertTrue(all(row["cost_usd"] == row["time_seconds"] == "" for row in rows))
        missing = {r["task"] for r in rows if r["failure_category"] == "missing deliverable"}
        self.assertEqual(missing, {"foundation-strategy", "solar-witness-test-package"})
        self.assertEqual(sum(r["prompt_tokens"] != "" for r in rows), 3)
        self.assertTrue(all(r["discipline"] for r in rows))


if __name__ == "__main__":
    unittest.main()
