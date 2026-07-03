from __future__ import annotations

import sys
from dotenv import load_dotenv
from src.orchestrator import Orchestrator

load_dotenv()
def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python -m src.main "<your task>"')
        sys.exit(1)

    user_request = " ".join(sys.argv[1:])
    orchestrator = Orchestrator()

    print(f"\n VibeOps — Task: {user_request}\n{'-' * 60}")
    state = orchestrator.run(user_request)

    for msg in state.messages:
        status_icon = "OK" if msg.status.value == "success" else "FAIL"
        print(f"[{status_icon}] {msg.role.value} ({msg.latency_ms}ms)")

    print(f"{'-' * 60}\n")

    if state.failed:
        print("Workflow failed. Partial results below:\n")
    print(state.final_output or "No final output produced.")


if __name__ == "__main__":
    main()
