# frontend/components/sidebar.py
import streamlit as st
from frontend.components.status import render_status
from frontend.components.chat import run_async_sync

def render_sidebar():
    with st.sidebar:
        st.markdown("# ✦ XENO")
        st.markdown("#### BUILD BEYOND LIMITS.")
        st.markdown("*Local Developer Intelligence*")
        st.markdown("---")

        # Model and Feature Configuration
        st.markdown("### 🛠️ Configuration")
        
        # Load available models
        mm = st.session_state.model_manager
        try:
            available_models = run_async_sync(mm.list_models(refresh=True))
        except Exception:
            available_models = []
            
        default_model = "qwen3.5:0.8b"
        if not available_models:
            available_models = [default_model]
            
        # Select active model
        active_model = st.selectbox(
            "Active LLM",
            available_models,
            index=0 if default_model not in available_models else available_models.index(default_model),
            help="Select the model for text generation."
        )
        st.session_state.active_model = active_model
        
        # RAG and Long term memory toggles
        col1, col2 = st.columns(2)
        with col1:
            rag_enabled = st.toggle("RAG Search", value=False, help="Inject knowledge from data/knowledge folder.")
            st.session_state.rag_enabled = rag_enabled
        with col2:
            lt_enabled = st.toggle("Memory", value=False, help="Retrieve facts from long-term memory store.")
            st.session_state.long_term_enabled = lt_enabled
            
        st.markdown("---")

        # New Chat button
        if st.button("➕ New Chat", use_container_width=True):
            # Create new conversation
            chat_mgr = st.session_state.chat_manager
            conv = run_async_sync(chat_mgr.create_conversation(model=active_model))
            st.session_state.current_conversation = conv.id
            st.session_state.messages = []
            st.session_state.loaded_conversation_id = conv.id
            st.rerun()

        st.markdown("### Conversations")
        # List conversations
        chat_mgr = st.session_state.chat_manager
        conversations = run_async_sync(chat_mgr.list_conversations())
        for conv in conversations:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                # Highlight active conversation
                label = f"✨ {conv.title}" if conv.id == st.session_state.current_conversation else conv.title
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