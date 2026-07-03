from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.code_agent import CodeAgent
from src.agents.doc_agent import DocAgent
from src.agents.research_agent import ResearchAgent
from src.agents.test_agent import TestAgent
from src.memory import SharedMemory
from src.schema import TaskStatus, WorkflowState


class Orchestrator:
    def __init__(self, memory: SharedMemory | None = None):
        self.memory = memory or SharedMemory()
        self.research_agent = ResearchAgent()
        self.code_agent = CodeAgent()
        self.test_agent = TestAgent()
        self.doc_agent = DocAgent()
        self.graph = self._build_graph()

    def _research_node(self, state: WorkflowState) -> WorkflowState:
        state.step_count += 1
        recalled = self.memory.recall(state.user_request)
        context = "\n".join(recalled) if recalled else ""
        msg = self.research_agent.run(state.user_request, context=context)
        msg.task_id = state.task_id
        self.memory.record(msg)
        state.messages.append(msg)
        if msg.status == TaskStatus.FAILED:
            state.failed = True
        else:
            state.research_notes = msg.output
        return state

    def _code_node(self, state: WorkflowState) -> WorkflowState:
        state.step_count += 1
        msg = self.code_agent.run(
            state.user_request, context=state.research_notes or ""
        )
        msg.task_id = state.task_id
        self.memory.record(msg)
        state.messages.append(msg)
        if msg.status == TaskStatus.FAILED:
            state.failed = True
        else:
            state.generated_code = msg.output
        return state

    def _test_node(self, state: WorkflowState) -> WorkflowState:
        state.step_count += 1
        msg = self.test_agent.run(
            state.user_request, context=state.generated_code or ""
        )
        msg.task_id = state.task_id
        self.memory.record(msg)
        state.messages.append(msg)
        if msg.status == TaskStatus.FAILED:
            state.failed = True
        else:
            state.test_results = msg.output
        return state

    def _doc_node(self, state: WorkflowState) -> WorkflowState:
        state.step_count += 1
        combined_context = f"{state.generated_code}\n\n{state.test_results}"
        msg = self.doc_agent.run(state.user_request, context=combined_context)
        msg.task_id = state.task_id
        self.memory.record(msg)
        state.messages.append(msg)
        if msg.status == TaskStatus.FAILED:
            state.failed = True
        else:
            state.documentation = msg.output
            state.final_output = (
                f"## Code\n{state.generated_code}\n\n"
                f"## Tests\n{state.test_results}\n\n"
                f"## Docs\n{state.documentation}"
            )
        return state

    def _route_after(self, state: WorkflowState) -> str:
        if state.failed or state.step_count >= state.max_steps:
            return "end"
        return "continue"

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("research", self._research_node)
        graph.add_node("code", self._code_node)
        graph.add_node("test", self._test_node)
        graph.add_node("doc", self._doc_node)

        graph.set_entry_point("research")
        graph.add_conditional_edges(
            "research", self._route_after, {"continue": "code", "end": END}
        )
        graph.add_conditional_edges(
            "code", self._route_after, {"continue": "test", "end": END}
        )
        graph.add_conditional_edges(
            "test", self._route_after, {"continue": "doc", "end": END}
        )
        graph.add_edge("doc", END)

        return graph.compile()

    def run(self, user_request: str) -> WorkflowState:
        initial_state = WorkflowState(user_request=user_request)
        result = self.graph.invoke(initial_state)
        return WorkflowState(**result)
