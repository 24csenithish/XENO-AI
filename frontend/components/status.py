# frontend/components/status.py
import streamlit as st
from frontend.components.chat import run_async_sync


def render_status():
    mm = st.session_state.model_manager
    try:
        models = run_async_sync(mm.list_models())
        role_status = run_async_sync(mm.get_model_status())
    except Exception:
        models = []
        role_status = {}

    st.markdown("### Status")
    if models:
        st.success(f"Ollama: {len(models)} models online")
    else:
        st.warning("Ollama not detected")

    ready_roles = [r for r, s in role_status.items() if s == "AVAILABLE"]
    if ready_roles:
        st.caption(f"Intelligence engines ready: {', '.join(ready_roles)}")
    elif role_status:
        st.caption("No configured intelligence engines installed yet.")

    mode = st.session_state.get("active_model")
    if mode:
        st.caption(f"Override: {mode}")
    else:
        st.caption("Mode: Auto-routing enabled")
