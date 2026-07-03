from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    CODE = "code"
    TEST = "test"
    DOC = "doc"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class AgentMessage(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: AgentRole
    input: str
    context: dict[str, Any] = Field(default_factory=dict)
    output: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    latency_ms: Optional[int] = None

    def mark_success(self, output: str, latency_ms: int) -> "AgentMessage":
        self.output = output
        self.status = TaskStatus.SUCCESS
        self.latency_ms = latency_ms
        return self

    def mark_failed(self, error: str, latency_ms: int) -> "AgentMessage":
        self.error = error
        self.status = TaskStatus.FAILED
        self.latency_ms = latency_ms
        return self


class WorkflowState(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_request: str
    messages: list[AgentMessage] = Field(default_factory=list)
    research_notes: Optional[str] = None
    generated_code: Optional[str] = None
    test_results: Optional[str] = None
    documentation: Optional[str] = None
    step_count: int = 0
    max_steps: int = 10
    failed: bool = False
    final_output: Optional[str] = None
