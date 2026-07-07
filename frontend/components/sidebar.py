# frontend/components/sidebar.py
import streamlit as st
from frontend.components.status import render_status
from frontend.components.chat import run_async_sync

AUTO_ROUTE_LABEL = "Auto (XENO decides)"


def render_sidebar():
    with st.sidebar:
        st.markdown("# ✦ XENO")
        st.markdown("#### BUILD BEYOND LIMITS.")
        st.markdown("*Local Developer Intelligence*")
        st.markdown("---")

        st.markdown("### 🛠️ Configuration")

        mm = st.session_state.model_manager
        try:
            available_models = run_async_sync(mm.list_models(refresh=True))
        except Exception:
            available_models = []

        mode_options = [AUTO_ROUTE_LABEL]
        if available_models:
            mode_options.extend(available_models)

        current = st.session_state.get("active_model")
        default_index = 0
        if current and current in available_models:
            default_index = mode_options.index(current)

        selected = st.selectbox(
            "Intelligence Mode",
            mode_options,
            index=default_index,
            help="Auto mode lets XENO select the best local model for each message.",
        )

        if selected == AUTO_ROUTE_LABEL:
            st.session_state.active_model = None
        else:
            st.session_state.active_model = selected

        st.session_state.developer_mode = st.toggle(
            "Developer Mode",
            value=st.session_state.get("developer_mode", False),
            help="Show routing role, model name, and confidence.",
        )

        col1, col2 = st.columns(2)
        with col1:
            rag_enabled = st.toggle(
                "RAG Search",
                value=False,
                help="Inject knowledge from data/knowledge folder.",
            )
            st.session_state.rag_enabled = rag_enabled
        with col2:
            lt_enabled = st.toggle(
                "Memory",
                value=False,
                help="Retrieve facts from long-term memory store.",
            )
            st.session_state.long_term_enabled = lt_enabled

        st.markdown("---")

        active_for_conv = st.session_state.get("active_model") or "auto"
        if st.button("➕ New Chat", use_container_width=True):
            chat_mgr = st.session_state.chat_manager
            conv = run_async_sync(chat_mgr.create_conversation(model=active_for_conv))
            st.session_state.current_conversation = conv.id
            st.session_state.messages = []
            st.session_state.loaded_conversation_id = conv.id
            st.rerun()

        st.markdown("### Conversations")
        chat_mgr = st.session_state.chat_manager
        conversations = run_async_sync(chat_mgr.list_conversations())
        for conv in conversations:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                label = (
                    f"✨ {conv.title}"
                    if conv.id == st.session_state.current_conversation
                    else conv.title
                )
                if st.button(label, key=f"conv_{conv.id}", use_container_width=True):
                    st.session_state.current_conversation = conv.id
                    st.session_state.loaded_conversation_id = None
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv.id}"):
                    run_async_sync(chat_mgr.delete_conversation(conv.id))
                    if st.session_state.current_conversation == conv.id:
                        st.session_state.current_conversation = None
                        st.session_state.messages = []
                        st.session_state.loaded_conversation_id = None
                    st.rerun()

        st.markdown("---")
        render_status()
    return st.session_state.current_conversation
