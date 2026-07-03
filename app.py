import streamlit as st
from dotenv import load_dotenv

from src.orchestrator import Orchestrator

load_dotenv()

st.set_page_config(page_title="VibeOps", layout="wide")
st.title("VibeOps")
st.caption("Research → Code → Test → Doc, one orchestrator, shared memory.")

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

user_request = st.text_area(
    "Describe the task", placeholder="Build a function that validates email addresses"
)

if st.button("Run", type="primary") and user_request:
    with st.spinner("Agents working..."):
        state = st.session_state.orchestrator.run(user_request)

    cols = st.columns(4)
    labels = ["Research", "Code", "Test", "Doc"]
    for col, label, msg in zip(cols, labels, state.messages):
        with col:
            icon = "✅" if msg.status.value == "success" else "❌"
            st.metric(label, f"{icon} {msg.latency_ms}ms")

    if state.failed:
        st.error("Workflow failed partway through. Showing partial results.")
    else:
        st.success("Workflow completed.")

    st.markdown(state.final_output or "No output produced.")

    with st.expander("Raw agent trace (shared memory)"):
        for msg in state.messages:
            st.json(msg.model_dump())
