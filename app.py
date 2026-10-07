"""
Main Entrypoint for Merchant Pricing Operations & Approval Platform.
Run with: streamlit run app.py
"""
import streamlit as st
import os

# Page Config
st.set_page_config(
    page_title="Merchant Pricing Operations Platform",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database & Seed Data
from src.database import init_db, DB_FILE
from src.seed_data import seed_all_data

if not os.path.exists(DB_FILE):
    init_db()
    seed_all_data()
else:
    init_db() # Ensure schema present

# Inject CSS Styling
from src.utils import inject_custom_css
inject_custom_css()

# Import Page Renderers
from pages.dashboard import render_dashboard
from pages.pricing_requests import render_pricing_requests
from pages.pricing_configuration import render_pricing_configuration
from pages.margin_analysis import render_margin_analysis
from pages.approvals import render_approvals
from pages.tickets import render_tickets
from pages.audit_log import render_audit_log
from pages.reports import render_reports
from pages.admin_settings import render_admin_settings

# ==========================================
# SIDEBAR NAVIGATION & SIMULATED ROLES
# ==========================================
st.sidebar.markdown("### 💳 Merchant Pricing Ops")
st.sidebar.caption("Fintech Pricing Operations Simulation")
st.sidebar.markdown("---")

# Demo Role Selector
st.sidebar.markdown("#### 👤 Demo Role Selector")
demo_roles = [
    "Pricing Analyst",
    "POC Reviewer",
    "Banking Operations",
    "Checker",
    "Function Head",
    "Operations Admin"
]

if "demo_role" not in st.session_state:
    st.session_state["demo_role"] = "Pricing Analyst"

selected_role = st.sidebar.selectbox(
    "Active Role for Simulation:",
    demo_roles,
    index=demo_roles.index(st.session_state["demo_role"])
)
st.session_state["demo_role"] = selected_role

st.sidebar.info(f"Active Role: **{selected_role}**")
st.sidebar.markdown("---")

# Page Navigation Radio
st.sidebar.markdown("#### 🧭 Platform Navigation")
nav_selection = st.sidebar.radio(
    "Go to Page:",
    [
        "📊 Operations Dashboard",
        "📋 Pricing Requests Workbench",
        "⚙️ Merchant Pricing Configuration",
        "💰 Margin & Profitability Analysis",
        "✅ Approval Hierarchy Workbench",
        "🎫 Ticket Desk & Service Workflow",
        "📜 Audit Trail Explorer",
        "📈 Operational Reports",
        "⚙️ Admin & Policy Settings"
    ],
    index=0
)

st.sidebar.markdown("---")

# Reset Demo Data Button in Sidebar
if st.sidebar.button("🔄 Reset Demo Data"):
    from src.database import reset_database
    reset_database()
    st.sidebar.success("Demo data reset complete!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("""
**Disclaimer:**  
This is a portfolio simulation of fintech pricing operations.  
Not affiliated with or connected to Razorpay, Salesforce, Freshdesk, or banking APIs.
""")

# ==========================================
# MAIN PAGE ROUTING
# ==========================================
if nav_selection == "📊 Operations Dashboard":
    render_dashboard()
elif nav_selection == "📋 Pricing Requests Workbench":
    render_pricing_requests(selected_role)
elif nav_selection == "⚙️ Merchant Pricing Configuration":
    render_pricing_configuration()
elif nav_selection == "💰 Margin & Profitability Analysis":
    render_margin_analysis(selected_role)
elif nav_selection == "✅ Approval Hierarchy Workbench":
    render_approvals(selected_role)
elif nav_selection == "🎫 Ticket Desk & Service Workflow":
    render_tickets(selected_role)
elif nav_selection == "📜 Audit Trail Explorer":
    render_audit_log()
elif nav_selection == "📈 Operational Reports":
    render_reports()
elif nav_selection == "⚙️ Admin & Policy Settings":
    render_admin_settings(selected_role)
