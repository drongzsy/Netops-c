"""RAG Engine — 配置语义搜索与知识库问答。

基于向量检索 + LLM 生成，支持：
- 设备配置全文语义搜索
- 故障案例知识库问答
- 运维文档智能检索
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

# ── 向量检索（预留接口） ──────────────────────────────────────────


class VectorStore:
    """向量存储抽象层，后续可接入 Chroma/Qdrant 等。"""

    def __init__(self):
        self._docs: list[dict] = []

    def add_documents(self, docs: list[dict]) -> None:
        self._docs.extend(docs)

    def similarity_search(self, query: str, top_k: int = 5) -> list[dict]:
        """简易关键词匹配，后续替换为向量检索。"""
        results = []
        query_lower = query.lower()
        for doc in self._docs:
            text = doc.get("text", "").lower()
            if query_lower in text:
                results.append(doc)
        return results[:top_k]


# ── RAG 引擎 ──────────────────────────────────────────────────────


class RAGEngine:
    """检索增强生成引擎。"""

    def __init__(self, db: Session | None = None):
        self.db = db
        self.vector_store = VectorStore()
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        """加载本地知识库（故障案例、运维文档等）。"""
        # TODO: 从数据库或文件加载知识库
        pass

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """检索相关文档片段。"""
        return self.vector_store.similarity_search(query, top_k)

    def generate(self, query: str, context: list[dict]) -> str:
        """基于检索结果生成回答（预留 LLM 接口）。"""
        # TODO: 接入 LLM（Claude/GPT API）
        sources = "\n".join(
            f"- {doc.get('source', 'unknown')}" for doc in context
        )
        return (
            f"基于 {len(context)} 条相关记录生成回答。\n"
            f"问题: {query}\n"
            f"参考来源:\n{sources}"
        )

    def query(self, question: str) -> dict[str, Any]:
        """完整 RAG 查询流程：检索 → 生成。"""
        docs = self.retrieve(question)
        answer = self.generate(question, docs)
        return {
            "success": True,
            "answer": answer,
            "sources": [d.get("source") for d in docs],
            "timestamp": datetime.utcnow().isoformat(),
        }


# ── 单例 ──────────────────────────────────────────────────────────

_engine: RAGEngine | None = None


def get_engine(db: Session | None = None) -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine(db)
    return _engine
