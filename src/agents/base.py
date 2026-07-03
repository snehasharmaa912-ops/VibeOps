from __future__ import annotations

import os
import time
from typing import Optional

from anthropic import Anthropic, APIError

from src.schema import AgentMessage, AgentRole, TaskStatus

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_RETRIES = 2
BACKOFF_SECONDS = 2


class BaseAgent:
    role: AgentRole = AgentRole.ORCHESTRATOR
    system_prompt: str = "You are a helpful assistant."

    def __init__(self, client: Optional[Anthropic] = None):
        self.client = client or Anthropic()

    def _call_model(self, user_input: str, context: str = "") -> str:
        full_input = f"{context}\n\n---\n\nTask:\n{user_input}" if context else user_input
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=self.system_prompt,
            messages=[{"role": "user", "content": full_input}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        )

    def run(self, task_input: str, context: str = "") -> AgentMessage:
        message = AgentMessage(role=self.role, input=task_input, status=TaskStatus.RUNNING)
        start = time.time()
        last_error = None

        for attempt in range(1, MAX_RETRIES + 2):
            try:
                output = self._call_model(task_input, context)
                latency_ms = int((time.time() - start) * 1000)
                return message.mark_success(output, latency_ms)
            except (APIError, Exception) as e:  # noqa: BLE001
                last_error = str(e)
                if attempt <= MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS * attempt)
                continue

        latency_ms = int((time.time() - start) * 1000)
        return message.mark_failed(last_error or "unknown error", latency_ms)
