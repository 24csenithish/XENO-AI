# frontend/components/status.py
import streamlit as st
from frontend.components.chat import run_async_sync

def render_status():
    # Lazy import to avoid circular dependency
    from app.llm.model_manager import ModelManager
    mm = ModelManager()
    try:
        models = run_async_sync(mm.list_models())
    except Exception:
        models = []
    
    st.markdown("### Status")
    if models:
        st.success(f"Ollama: {len(models)} models online")
    else:
        st.warning("Ollama not detected")
    st.caption(f"Default Model: {st.session_state.get('active_model', 'qwen3.5:0.8b')}")