import io
import tempfile
import unittest
from pathlib import Path

from make_figures import design_figures, evidence_figures, read_results


HEADER = "config,model,task_id,repeat,score,cost_usd,failure_category\n"


class FigureTests(unittest.TestCase):
    def test_reads_and_renders_measured_rows(self):
        rows = read_results(io.StringIO(HEADER + "test,mock-fixture,t1,1,0.5,0.1,units\n"
                                       "test,mock-fixture,t2,1,1,0.2,\n"))
        self.assertEqual([r["score"] for r in rows], [0.5, 1])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            evidence_figures(output, rows)
            self.assertEqual(len(list(output.glob("*.png"))), 2)
            self.assertTrue(all(p.stat().st_size > 1000 for p in output.glob("*.png")))

    def test_empty_results_are_not_measurements(self):
        for text in ("", HEADER):
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_results(io.StringIO(text))

    def test_invalid_measurements_are_rejected(self):
        for row in ("x,m,t,1,nan,0,", "x,m,t,1,1,inf,", "x,m,t,1,-1,0,",
                    "x,m,t,1,1,-1,", "x,m,t,1,2,0,", "x,m,t,1,no,0,", "x,m,,1,1,0,"):
            with self.subTest(row=row), self.assertRaises(ValueError):
                read_results(io.StringIO(HEADER + row + "\n"))
        with self.assertRaises(ValueError):
            read_results(io.StringIO(HEADER + "x,m,t,1,1,0,\nx,m,t,1,1,0,\n"))

    def test_no_data_renders_clearly_marked_panels_and_design(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            design_figures(output)
            evidence_figures(output, None)
            self.assertEqual({p.name for p in output.glob("*.png")}, {
                "architecture.png", "cover.png", "score-vs-cost.png", "failure-breakdown.png"})

    def test_all_perfect_rows_have_no_failure_bars(self):
        rows = read_results(io.StringIO(HEADER + "test,mock-fixture,t1,1,1,0,\n"))
        with tempfile.TemporaryDirectory() as directory:
            evidence_figures(Path(directory), rows)


if __name__ == "__main__":
    unittest.main()
