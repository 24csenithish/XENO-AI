"""Streamlit frontend for XENO AI."""

import logging
import os
import sys

import streamlit as st

# Add project root to path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat.chat_manager import ChatManager
from app.llm.model_manager import ModelManager
from frontend.components.chat import render_chat_area
from frontend.components.header import render_header
from frontend.components.sidebar import render_sidebar
from frontend.styles.xeno_css import load_css

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="✦ XENO AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_css()

# Initialize session state
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()
if "model_manager" not in st.session_state:
    st.session_state.model_manager = ModelManager()
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = None
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts for UI
if "loaded_conversation_id" not in st.session_state:
    st.session_state.loaded_conversation_id = None

# Sidebar
conversation_id = render_sidebar()

# Main chat area
render_chat_area(conversation_id)

# Footer
st.markdown("---")
st.caption("XENO AI • Local Intelligence • Ollama")