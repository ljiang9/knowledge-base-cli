# knowledge-base-cli

零第三方依赖的命令行知识库：把目录下的文档**建索引并持久化**，支持**增量添加**与 **top-k 查询**。

## 功能简介

- 递归收录目录下的 `.txt` / `.md` 文档，建 TF-IDF 语义索引；
- 索引以**可读 JSON** 持久化到磁盘，随时重新加载；
- **增量添加**：在已有索引上追加新文档，并更新逆文档频率统计；
- 查询用余弦相似度返回 top-k 相关文档，附带来源路径与预览。

## 快速开始

```bash
# 1) 从一个目录建库
python3 cli.py build ./my_docs

# 2) 之后增量添加新文档（在已有索引上追加）
python3 cli.py add ./new_note.md

# 3) 查询
python3 cli.py query "怎么训练机器学习模型" --k 3
```

可用 `--index path.json` 指定索引文件位置（默认 `./kb_index.json`）。

## 无 API key 如何运行

本项目**完全不需要 API key**。建库、持久化、增量、查询全部本地完成。

## 目录说明

```
knowledge-base-cli/
├── knowledgebase.py     # 核心库：KnowledgeBase（add/save/load/query）
├── cli.py               # build / add / query 子命令
├── tests/test_kb.py     # unittest 测试（含临时目录与持久化往返）
└── README.md
```

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT License，Copyright (c) 2026 ljiang9
