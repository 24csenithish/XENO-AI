# frontend/components/header.py
import streamlit as st


def render_header():
    st.markdown("### ✦ XENO AI")

    col1, col2 = st.columns([0.7, 0.3])
    with col2:
        st.markdown("🟢 Online")

    engine_info = st.session_state.get("last_engine_info")
    developer_mode = st.session_state.get("developer_mode", False)

    if engine_info and engine_info.get("role"):
        role = engine_info["role"].upper()
        if developer_mode:
            model = engine_info.get("model", "unknown")
            confidence = engine_info.get("confidence")
            conf_text = f" · {confidence:.0%}" if confidence else ""
            st.caption(f"Engine: {role} · Model: {model}{conf_text}")
        else:
            st.caption(f"Engine: {role}")
