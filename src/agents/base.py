from __future__ import annotations

import os
import time
from typing import Optional

from groq import Groq

from src.schema import AgentMessage, AgentRole, TaskStatus

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_RETRIES = 2
BACKOFF_SECONDS = 2


class BaseAgent:
    role: AgentRole = AgentRole.ORCHESTRATOR
    system_prompt: str = "You are a helpful assistant."

    def __init__(self, client: Optional[Groq] = None):
        self.client = client or Groq()

    def _call_model(self, user_input: str, context: str = "") -> str:
        full_input = f"{context}\n\n---\n\nTask:\n{user_input}" if context else user_input
        response = self.client.chat.completions.create(
            model=MODEL,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": full_input},
            ],
        )
        return response.choices[0].message.content

    def run(self, task_input: str, context: str = "") -> AgentMessage:
        message = AgentMessage(role=self.role, input=task_input, status=TaskStatus.RUNNING)
        start = time.time()
        last_error = None

        for attempt in range(1, MAX_RETRIES + 2):
            try:
                output = self._call_model(task_input, context)
                latency_ms = int((time.time() - start) * 1000)
                return message.mark_success(output, latency_ms)
            except Exception as e:  # noqa: BLE001
                last_error = str(e)
                if attempt <= MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS * attempt)
                continue

        latency_ms = int((time.time() - start) * 1000)
        return message.mark_failed(last_error or "unknown error", latency_ms)
