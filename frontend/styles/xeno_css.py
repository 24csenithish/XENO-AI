# frontend/styles/xeno_css.py
import streamlit as st

def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Outfit:wght@300;400;600&family=Share+Tech+Mono&display=swap');

        /* Cyberpunk Theme Stylesheet */
        
        /* Apply fonts globally */
        .stApp {
            background: radial-gradient(circle at 50% 50%, #0d0918 0%, #030206 100%) !important;
            color: #00f3ff !important;
            font-family: 'Outfit', sans-serif !important;
        }

        /* Futuristic scanline and grid overlay */
        .stApp::before {
            content: " ";
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: 
                linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
            background-size: 30px 30px;
            z-index: 0;
            pointer-events: none;
        }
        
        /* Animated scanline bar */
        .stApp::after {
            content: " ";
            position: fixed;
            top: 0; left: 0; right: 0; height: 100%;
            background: linear-gradient(
                to bottom,
                rgba(255, 0, 85, 0) 0%,
                rgba(255, 0, 85, 0.03) 10%,
                rgba(255, 0, 85, 0.08) 50%,
                rgba(255, 0, 85, 0.03) 90%,
                rgba(255, 0, 85, 0) 100%
            );
            background-size: 100% 6px;
            z-index: 9999;
            pointer-events: none;
            opacity: 0.4;
            animation: scanline 12s linear infinite;
        }

        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
        }

        /* Headings */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Orbitron', sans-serif !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            color: #ff0055 !important;
            text-shadow: 0 0 10px rgba(255, 0, 85, 0.4), 0 0 20px rgba(255, 0, 85, 0.1) !important;
        }

        .stMarkdown {
            color: #d1cbe3 !important;
        }

        /* Sidebar Styling */
        .stSidebar {
            background-color: #05040a !important;
            border-right: 2px solid #ff0055 !important;
            box-shadow: 5px 0 15px rgba(255, 0, 85, 0.2) !important;
        }

        .stSidebar [data-testid="stMarkdownContainer"] h1 {
            color: #00f3ff !important;
            text-shadow: 0 0 10px rgba(0, 243, 255, 0.4) !important;
        }

        /* Cyberpunk Button System */
        .stButton button {
            background: linear-gradient(135deg, #ff0055 0%, #7a0099 100%) !important;
            color: #ffffff !important;
            font-family: 'Orbitron', sans-serif !important;
            text-transform: uppercase !important;
            font-weight: 700 !important;
            letter-spacing: 2px !important;
            border: 1px solid #ff0055 !important;
            box-shadow: 0 0 10px rgba(255, 0, 85, 0.3) !important;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            border-radius: 2px !important;
            margin-top: 4px;
        }

        .stButton button:hover {
            background: linear-gradient(135deg, #00f3ff 0%, #7a0099 100%) !important;
            border-color: #00f3ff !important;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.6) !important;
            transform: translateY(-2px) !important;
            color: #ffffff !important;
        }

        .stSidebar .stButton button {
            background: rgba(10, 10, 20, 0.6) !important;
            color: #00f3ff !important;
            border: 1px solid rgba(0, 243, 255, 0.3) !important;
            box-shadow: none !important;
            text-align: left !important;
        }

        .stSidebar .stButton button:hover {
            background: rgba(0, 243, 255, 0.15) !important;
            border-color: #00f3ff !important;
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.4) !important;
            color: #ffffff !important;
        }

        /* Custom Chat Bubbles */
        div[data-testid="stChatMessage"] {
            background-color: rgba(13, 10, 24, 0.7) !important;
            backdrop-filter: blur(10px);
            border-radius: 4px !important;
            padding: 16px !important;
            margin-bottom: 14px !important;
            border: 1px solid rgba(255, 0, 85, 0.25) !important;
            border-left: 4px solid #ff0055 !important;
            box-shadow: 0 0 15px rgba(255, 0, 85, 0.1) !important;
            animation: chatSlideIn 0.4s ease-out forwards;
        }

        /* Distinguish User bubble if avatar/content class matches */
        div[data-testid="stChatMessage"]:nth-child(even) {
            border-left: 4px solid #00f3ff !important;
            border-color: rgba(0, 243, 255, 0.25) !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.1) !important;
        }

        @keyframes chatSlideIn {
            from {
                opacity: 0;
                transform: translateY(15px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Code Block Styling */
        .stCodeBlock {
            background-color: #07050d !important;
            border: 1px solid rgba(255, 0, 85, 0.3) !important;
            border-radius: 2px !important;
            font-family: 'Share Tech Mono', monospace !important;
            box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.8) !important;
        }

        /* Input Controls */
        div[data-testid="stChatInput"] {
            background-color: rgba(10, 8, 20, 0.9) !important;
            border: 1px solid #ff0055 !important;
            box-shadow: 0 0 15px rgba(255, 0, 85, 0.25) !important;
            border-radius: 4px !important;
        }

        div[data-testid="stChatInput"]:focus-within {
            border-color: #00f3ff !important;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.5) !important;
        }

        textarea[data-testid="stChatInputTextArea"] {
            background-color: transparent !important;
            color: #ffffff !important;
            font-family: 'Share Tech Mono', monospace !important;
        }

        /* Selection and checkboxes styling */
        div[data-testid="stSelectbox"] select, div[data-testid="stSelectbox"] div[role="button"] {
            background-color: #0d0a18 !important;
            color: #00f3ff !important;
            border: 1px solid rgba(0, 243, 255, 0.4) !important;
            font-family: 'Share Tech Mono', monospace !important;
        }
        
        div[data-testid="stSelectbox"] label, div[data-testid="stToggle"] label {
            color: #00f3ff !important;
            font-family: 'Orbitron', sans-serif !important;
            font-size: 0.8rem !important;
            letter-spacing: 1px !important;
        }

        /* Toggles styling */
        .stToggle>div {
            background-color: #1a1a2e !important;
        }
    </style>
    """, unsafe_allow_html=True)