# frontend/components/header.py
import streamlit as st

def render_header():
    st.markdown("### ✦ XENO")
    # Status indicator
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        st.markdown("🟢 Online")