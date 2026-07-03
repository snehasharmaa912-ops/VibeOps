from src.agents.base import BaseAgent
from src.schema import AgentRole


class DocAgent(BaseAgent):
    role = AgentRole.DOC
    system_prompt = (
        "You are a Documentation Agent in a multi-agent engineering system. "
        "Given generated code and its tests, write concise Markdown "
        "documentation: what it does, usage example, and parameters. "
        "Keep it under 150 words."
    )
