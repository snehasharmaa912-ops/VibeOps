import tempfile
from pathlib import Path

import pytest

from src.memory import SharedMemory
from src.schema import AgentMessage, AgentRole, TaskStatus


@pytest.fixture
def shared_memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.sqlite")
        vector_dir = str(Path(tmpdir) / "chroma")
        yield SharedMemory(db_path=db_path, vector_dir=vector_dir)


def test_working_memory_records_message(shared_memory):
    msg = AgentMessage(
        role=AgentRole.RESEARCH,
        input="test task",
        status=TaskStatus.SUCCESS,
        output="test output",
        latency_ms=100,
    )
    shared_memory.record(msg)
    history = shared_memory.task_history(msg.task_id)

    assert len(history) == 1
    assert history[0]["output"] == "test output"
    assert history[0]["status"] == "success"


def test_failed_messages_are_not_indexed_for_recall(shared_memory):
    msg = AgentMessage(
        role=AgentRole.CODE,
        input="test task",
        status=TaskStatus.FAILED,
        error="API error",
        latency_ms=50,
    )
    shared_memory.record(msg)
    results = shared_memory.recall("test task")

    assert results == []


def test_successful_messages_are_recallable(shared_memory):
    msg = AgentMessage(
        role=AgentRole.RESEARCH,
        input="email validation",
        status=TaskStatus.SUCCESS,
        output="Use regex for basic email validation with RFC 5322 pattern.",
        latency_ms=200,
    )
    shared_memory.record(msg)
    results = shared_memory.recall("email validation approach")

    assert len(results) >= 1
    assert "regex" in results[0].lower() or "email" in results[0].lower()


def test_task_history_is_ordered(shared_memory):
    task_id = "shared-task-123"
    for i, role in enumerate([AgentRole.RESEARCH, AgentRole.CODE, AgentRole.TEST]):
        msg = AgentMessage(
            task_id=task_id,
            role=role,
            input=f"step {i}",
            status=TaskStatus.SUCCESS,
            output=f"output {i}",
            latency_ms=10,
        )
        shared_memory.record(msg)

    history = shared_memory.task_history(task_id)
    assert [h["role"] for h in history] == ["research", "code", "test"]
