"""Streamlit frontend for XENO AI."""

import logging
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat.chat_manager import ChatManager
from app.llm.model_manager import ModelManager
from app.llm.startup import run_startup_model_check
from frontend.components.chat import render_chat_area, run_async_sync
from frontend.components.sidebar import render_sidebar
from frontend.styles.xeno_css import load_css

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="✦ XENO AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()
if "model_manager" not in st.session_state:
    st.session_state.model_manager = ModelManager()
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "loaded_conversation_id" not in st.session_state:
    st.session_state.loaded_conversation_id = None
if "developer_mode" not in st.session_state:
    st.session_state.developer_mode = False
if "last_engine_info" not in st.session_state:
    st.session_state.last_engine_info = None

if "startup_checked" not in st.session_state:
    try:
        run_async_sync(run_startup_model_check(st.session_state.model_manager.client))
    except Exception:
        pass
    st.session_state.startup_checked = True

conversation_id = render_sidebar()
render_chat_area(conversation_id)

st.markdown("---")
st.caption("XENO AI • Local Intelligence • Offline Multi-LLM")
