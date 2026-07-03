from src.agents.base import BaseAgent
from src.schema import AgentRole


class CodeAgent(BaseAgent):
    role = AgentRole.CODE
    system_prompt = (
        "You are a Coder Agent in a multi-agent engineering system. "
        "Given a task and a research brief, write clean, typed, production-"
        "quality Python code that solves it. Include docstrings. Output ONLY "
        "the code in a single fenced code block, no extra commentary."
    )
