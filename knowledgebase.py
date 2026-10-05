"""knowledgebase.py — 可持久化、可增量更新的本地知识库。

把一个目录下的文本文档建成语义索引（TF-IDF + 余弦），保存到 JSON；
之后可增量添加新文档（更新 df 统计），也可随时查询 top-k。
零第三方依赖，索引即 JSON 文件，便于审查与迁移。
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from typing import Dict, List, Sequence, Tuple

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]")
SUPPORTED_EXT = {".txt", ".md", ".markdown"}


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


class KnowledgeBase:
    def __init__(self, index_path: str = "kb_index.json") -> None:
        self.index_path = index_path
        self.docs: List[Dict] = []          # 每条: {"id","path","text","tokens"}
        self.df: Counter = Counter()

    # ---------- 写入 ----------
    def add_text(self, text: str, path: str = "<inline>") -> int:
        counts = Counter(tokenize(text))
        doc_id = len(self.docs)
        self.docs.append({
            "id": doc_id,
            "path": path,
            "text": text,
            "tokens": dict(counts),
        })
        for term in counts:
            self.df[term] += 1
        return doc_id

    def add_file(self, file_path: str) -> int:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return self.add_text(text, path=os.path.abspath(file_path))

    def index_directory(self, dir_path: str) -> int:
        """递归收录目录下所有受支持的文本文件，返回新增数量。"""
        added = 0
        for root, _dirs, files in os.walk(dir_path):
            for name in sorted(files):
                ext = os.path.splitext(name)[1].lower()
                if ext in SUPPORTED_EXT:
                    self.add_file(os.path.join(root, name))
                    added += 1
        return added

    # ---------- 持久化 ----------
    def save(self) -> None:
        data = {
            "docs": self.docs,
            "df": dict(self.df),
        }
        tmp = self.index_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, self.index_path)

    def load(self) -> bool:
        if not os.path.exists(self.index_path):
            return False
        with open(self.index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.docs = data["docs"]
        self.df = Counter(data["df"])
        return True

    # ---------- 查询 ----------
    def _vec(self, counts: Counter) -> Dict[str, float]:
        total = max(len(self.docs), 1)
        if not counts:
            return {}
        mx = max(counts.values())
        return {
            term: (c / mx) * (math.log((1 + total) / (1 + self.df.get(term, 0))) + 1.0)
            for term, c in counts.items()
        }

    @staticmethod
    def _cos(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(v * b.get(k, 0.0) for k, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def query(self, text: str, k: int = 3) -> List[Tuple[int, float, Dict]]:
        q = self._vec(Counter(tokenize(text)))
        if not q or not self.docs:
            return []
        scored = []
        for d in self.docs:
            dvec = self._vec(Counter(d["tokens"]))
            scored.append((d["id"], self._cos(q, dvec), d))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(i, s, d) for i, s, d in scored[:k]]

    def __len__(self) -> int:
        return len(self.docs)
