import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.agents.code_agent import CodeAgent
from src.agents.doc_agent import DocAgent
from src.agents.research_agent import ResearchAgent
from src.agents.test_agent import TestAgent as ProjectTestAgent
from src.memory import SharedMemory
from src.orchestrator import Orchestrator


def _fake_response(text: str):
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(content=[block])


def _make_fake_client(response_text: str = "fake output"):
    client = MagicMock()
    client.messages.create.return_value = _fake_response(response_text)
    return client


@pytest.fixture
def shared_memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.sqlite")
        vector_dir = str(Path(tmpdir) / "chroma")
        yield SharedMemory(db_path=db_path, vector_dir=vector_dir)


@pytest.fixture
def orchestrator(shared_memory):
    orch = Orchestrator(memory=shared_memory)
    orch.research_agent = ResearchAgent(client=_make_fake_client("research notes"))
    orch.code_agent = CodeAgent(client=_make_fake_client("def foo(): pass"))
    orch.test_agent = ProjectTestAgent(client=_make_fake_client("def test_foo(): assert True"))
    orch.doc_agent = DocAgent(client=_make_fake_client("# Docs\nUsage: foo()"))
    orch.graph = orch._build_graph()
    return orch


def test_full_pipeline_runs_all_agents(orchestrator):
    state = orchestrator.run("build a function")

    assert not state.failed
    assert state.step_count == 4
    assert len(state.messages) == 4
    assert [m.role.value for m in state.messages] == [
        "research",
        "code",
        "test",
        "doc",
    ]


def test_pipeline_stops_on_failure(shared_memory):
    orch = Orchestrator(memory=shared_memory)
    orch.research_agent = ResearchAgent(client=_make_fake_client("notes"))

    failing_client = MagicMock()
    failing_client.messages.create.side_effect = Exception("simulated API failure")
    orch.code_agent = CodeAgent(client=failing_client)
    orch.test_agent = ProjectTestAgent(client=_make_fake_client("unused"))
    orch.doc_agent = DocAgent(client=_make_fake_client("unused"))
    orch.graph = orch._build_graph()

    state = orch.run("build a function")

    assert state.failed
    assert len(state.messages) == 2
    assert state.messages[-1].status.value in ("failed",)


def test_final_output_contains_all_sections(orchestrator):
    state = orchestrator.run("build a function")

    assert "## Code" in state.final_output
    assert "## Tests" in state.final_output
    assert "## Docs" in state.final_output


def test_memory_is_populated_after_run(orchestrator, shared_memory):
    state = orchestrator.run("build a function")
    history = shared_memory.task_history(state.task_id)

    assert len(history) == 4
    assert all(h["status"] == "success" for h in history)
