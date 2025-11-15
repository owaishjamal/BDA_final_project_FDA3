#!/usr/bin/env python3
"""
Multi-page Streamlit dashboard for FDA-3-Stream project.
Pages: Project Overview, Real-time Dashboard
"""
import streamlit as st

# Configure page
st.set_page_config(
    page_title="FDA-3-Stream Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("📊 FDA-3-Stream")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate to:",
    ["📖 Project Overview", "📈 Real-time Dashboard"],
    index=0
)

if page == "📖 Project Overview":
    from pages import project_overview
    project_overview.show()
else:
    from pages import realtime_dashboard
    realtime_dashboard.show()

