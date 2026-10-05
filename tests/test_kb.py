import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledgebase import KnowledgeBase  # noqa: E402


class TestKnowledgeBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.idx = os.path.join(self.tmp.name, "kb.json")
        # 造两个文档
        self.f1 = os.path.join(self.tmp.name, "a.txt")
        self.f2 = os.path.join(self.tmp.name, "b.md")
        with open(self.f1, "w", encoding="utf-8") as f:
            f.write("机器学习需要大量标注数据来训练模型，提升泛化能力。")
        with open(self.f2, "w", encoding="utf-8") as f:
            f.write("今天天气晴朗，适合去公园散步和野餐。")

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_directory(self):
        kb = KnowledgeBase(self.idx)
        n = kb.index_directory(self.tmp.name)
        self.assertGreaterEqual(n, 2)
        self.assertEqual(len(kb), n)

    def test_save_load_roundtrip(self):
        kb = KnowledgeBase(self.idx)
        kb.index_directory(self.tmp.name)
        kb.save()
        self.assertTrue(os.path.exists(self.idx))

        kb2 = KnowledgeBase(self.idx)
        self.assertTrue(kb2.load())
        self.assertEqual(len(kb2), len(kb))

    def test_incremental_add(self):
        kb = KnowledgeBase(self.idx)
        kb.add_file(self.f1)
        kb.save()
        self.assertEqual(len(kb), 1)

        # 新实例加载后增量追加
        kb2 = KnowledgeBase(self.idx)
        kb2.load()
        kb2.add_file(self.f2)
        kb2.save()
        self.assertEqual(len(kb2), 2)

        kb3 = KnowledgeBase(self.idx)
        kb3.load()
        self.assertEqual(len(kb3), 2)

    def test_query_relevant(self):
        kb = KnowledgeBase(self.idx)
        kb.index_directory(self.tmp.name)
        hits = kb.query("模型如何训练数据", k=1)
        self.assertEqual(len(hits), 1)
        _id, score, d = hits[0]
        self.assertIn("训练", d["text"])

    def test_empty_query(self):
        kb = KnowledgeBase(self.idx)
        kb.index_directory(self.tmp.name)
        self.assertEqual(kb.query(""), [])

    def test_load_missing(self):
        kb = KnowledgeBase(os.path.join(self.tmp.name, "nope.json"))
        self.assertFalse(kb.load())


if __name__ == "__main__":
    unittest.main()
