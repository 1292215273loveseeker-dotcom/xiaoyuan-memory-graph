import unittest
from pathlib import Path

import relate

from xiaoyuan_memory_graph.ingest import seed_fixture
from xiaoyuan_memory_graph.queries import (
    constraints_for_turn,
    gate_trace,
    recall_session,
    scenario_stats,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "ten_question_regression_full.json"


class TestMemoryGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = relate.connect(":memory:")
        cls.stats = seed_fixture(cls.conn, FIXTURE, reset=True)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_a1_counts(self):
        self.assertEqual(self.stats["sessions"], 10)
        self.assertEqual(self.stats["turns"], 31)
        self.assertEqual(self.stats["checks"], 31)
        self.assertEqual(self.stats["issues"], 5)
        self.assertEqual(self.stats["repairs"], 5)

    def test_a2_recall_q1(self):
        result = recall_session(self.conn, "Q1")
        self.assertEqual(result["id"], "Q1")
        self.assertIn("端侧AI挑战赛", result["title"])
        self.assertEqual(result["turn_count"], 3)
        self.assertEqual(result["last_turn"]["id"], "Q1-T3")

    def test_a3_gate_trace_q8(self):
        rows = gate_trace(self.conn, "Q8")
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum(1 for row in rows if row["repaired"]), 2)
        issue_text = " ".join(
            issue for row in rows for issue in row.get("issues", [])
        )
        self.assertIn("路由", issue_text)

    def test_a4_scenario_stats(self):
        rows = scenario_stats(self.conn)
        by_name = {row["scenario"]: row for row in rows}
        self.assertEqual(by_name["memory"]["turns"], 4)
        self.assertEqual(by_name["routing"]["repairs"], 2)

    def test_a5_constraints_q1_t1(self):
        rows = constraints_for_turn(self.conn, "Q1-T1")
        self.assertGreaterEqual(len(rows), 3)
        text = " ".join(row["text"] for row in rows)
        self.assertIn("本地14B", text)
        self.assertIn("云端", text)
        self.assertIn("健康数据", text)


if __name__ == "__main__":
    unittest.main()
