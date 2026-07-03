from src.agents.base import BaseAgent
from src.schema import AgentRole


class TestAgent(BaseAgent):
    role = AgentRole.TEST
    system_prompt = (
        "You are a Test Agent in a multi-agent engineering system. "
        "Given generated Python code, write pytest unit tests covering the "
        "happy path and at least two edge cases. Output ONLY the test code "
        "in a single fenced code block, no extra commentary."
    )
