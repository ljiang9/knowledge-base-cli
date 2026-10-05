#!/usr/bin/env python3
"""cli.py — knowledge-base-cli 命令行入口。

子命令：
    build <目录>                 # 把目录下所有 .txt/.md 建索引并持久化
    add  <文件或目录>            # 增量添加（在已有索引上追加，更新统计）
    query "问题" [--k 3]         # 对已建索引做 top-k 查询

索引默认保存在 ./kb_index.json，可用 --index 指定。
"""
from __future__ import annotations

import argparse
import os
import sys

from knowledgebase import KnowledgeBase


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="可持久化、可增量更新的本地知识库")
    p.add_argument("--index", default="kb_index.json", help="索引文件路径，默认 kb_index.json")
    sub = p.add_subparsers(dest="cmd")

    pb = sub.add_parser("build", help="从目录建索引")
    pb.add_argument("dir")

    pa = sub.add_parser("add", help="增量添加文件或目录")
    pa.add_argument("path")

    pq = sub.add_parser("query", help="查询知识库")
    pq.add_argument("question")
    pq.add_argument("--k", type=int, default=3)

    args = p.parse_args(argv)

    kb = KnowledgeBase(index_path=args.index)
    existed = kb.load()
    if existed:
        print(f"[加载] 已有索引：{len(kb)} 篇文档 <- {args.index}")

    if args.cmd == "build":
        n = kb.index_directory(args.dir)
        kb.save()
        print(f"[建库] 新增 {n} 篇，总计 {len(kb)} 篇，已写入 {args.index}")
    elif args.cmd == "add":
        if os.path.isdir(args.path):
            n = kb.index_directory(args.path)
        else:
            kb.add_file(args.path)
            n = 1
        kb.save()
        print(f"[增量] 新增 {n} 篇，总计 {len(kb)} 篇，已写入 {args.index}")
    elif args.cmd == "query":
        if not kb.docs:
            print("知识库为空，请先 build 或 add。")
            return 1
        hits = kb.query(args.question, k=args.k)
        print(f"查询：{args.question}（共 {len(kb)} 篇，top-{len(hits)}）")
        for rank, (_id, score, d) in enumerate(hits, 1):
            preview = d["text"].replace("\n", " ")[:80]
            print(f"  {rank}. [score={score:.4f}] ({d['path']}) {preview}...")
    else:
        p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
