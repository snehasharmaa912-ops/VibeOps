from __future__ import annotations
import hashlib
import sqlite3
from pathlib import Path
from typing import Any, Optional
import chromadb
import numpy as np

from src.schema import AgentMessage

class SimpleHashingEmbedding:
    _DIM = 384

    def name(self) -> str:
        return "simple_hashing_embedding"
      
    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_query(self, input):
        if isinstance(input, list):
            return [self._embed(text) for text in input]
        return self._embed(input)

    def _embed(self, text: str) -> list[float]:
        vec = np.zeros(self._DIM, dtype=np.float32)
        for token in text.lower().split():
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            idx = h % self._DIM
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


class WorkingMemory:
    """Structured, per-task state store backed by SQLite."""

    def __init__(self, db_path: str = "working_memory.sqlite"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    input TEXT,
                    output TEXT,
                    status TEXT,
                    error TEXT,
                    timestamp TEXT,
                    latency_ms INTEGER
                )
                """
            )
            conn.commit()

    def write(self, message: AgentMessage) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO agent_messages
                (task_id, role, input, output, status, error, timestamp, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.task_id,
                    message.role.value,
                    message.input,
                    message.output,
                    message.status.value,
                    message.error,
                    message.timestamp,
                    message.latency_ms,
                ),
            )
            conn.commit()

    def history(self, task_id: str) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM agent_messages WHERE task_id = ? ORDER BY id ASC",
                (task_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def all_task_ids(self) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT DISTINCT task_id FROM agent_messages"
            ).fetchall()
            return [r[0] for r in rows]


class LongTermMemory:
    """Semantic memory backed by a local Chroma vector store."""

    def __init__(self, persist_dir: str = "chroma_db"):
        Path(persist_dir).mkdir(exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            "agent_memory", embedding_function=SimpleHashingEmbedding()
        )
        self._counter = self.collection.count()

    def add(self, text: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self._counter += 1
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[f"mem_{self._counter}"],
        )

    def search(self, query: str, n_results: int = 3) -> list[str]:
        if self.collection.count() == 0:
            return []
        n_results = min(n_results, self.collection.count())
        results = self.collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])
        return docs[0] if docs else []


class SharedMemory:
    """Facade combining both memory layers — this is what agents import."""

    def __init__(
        self,
        db_path: str = "working_memory.sqlite",
        vector_dir: str = "chroma_db",
    ):
        self.working = WorkingMemory(db_path)
        self.long_term = LongTermMemory(vector_dir)

    def record(self, message: AgentMessage) -> None:
        self.working.write(message)
        if message.status.value == "success" and message.output:
            self.long_term.add(
                text=message.output,
                metadata={"task_id": message.task_id, "role": message.role.value},
            )

    def recall(self, query: str, n_results: int = 3) -> list[str]:
        return self.long_term.search(query, n_results)

    def task_history(self, task_id: str) -> list[dict[str, Any]]:
        return self.working.history(task_id)
