"""
Operations Dashboard Page for Merchant Pricing Operations Platform.
Displays executive KPIs, workflow status metrics, risk breakdown, SLA alerts, and Plotly charts.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.workflow_engine import get_all_requests
from src.ticket_engine import get_all_tickets
from src.utils import format_inr_short, get_status_badge, get_risk_badge, get_sla_badge


def render_dashboard():
    st.markdown("## 📊 Operations & Pricing Governance Dashboard")
    st.caption("Real-time executive metrics, workflow performance, SLA monitoring, and margin distributions.")

    requests = get_all_requests()
    tickets = get_all_tickets()

    if not requests:
        st.warning("No pricing request data found. Click 'Reset Demo Data' in the sidebar to seed demo data.")
        return

    df_req = pd.DataFrame(requests)
    df_tkt = pd.DataFrame(tickets) if tickets else pd.DataFrame()

    # Calculate Top KPIs
    total_reqs = len(df_req)
    pending_reqs = len(df_req[df_req["status"].isin(["IN_PROGRESS", "DRAFT"])])
    approved_reqs = len(df_req[df_req["status"] == "APPROVED"])
    executed_reqs = len(df_req[df_req["status"] == "EXECUTED"])
    rejected_reqs = len(df_req[df_req["status"] == "REJECTED"])
    
    high_risk_reqs = len(df_req[df_req["risk_level"].isin(["HIGH RISK", "CRITICAL"])])
    sla_breaches = len(df_req[df_req["is_sla_breached"] == 1])

    # Display KPI Cards
    k1, k2, k3, k4, k5, k6 = st.columns(6)

    k1.metric("Total Requests", total_reqs, help="Total pricing revamp requests logged")
    k2.metric("In Review / Draft", pending_reqs, help="Requests currently progressing through review stages")
    k3.metric("Approved / Ready", approved_reqs, help="Approved by hierarchy, awaiting execution")
    k4.metric("Executed", executed_reqs, help="Applied to production pricing table")
    k5.metric("High / Critical Risk", high_risk_reqs, delta=f"{high_risk_reqs/total_reqs*100:.0f}% of total", delta_color="inverse")
    k6.metric("SLA Breaches", sla_breaches, delta=f"{sla_breaches} overdue", delta_color="inverse" if sla_breaches > 0 else "normal")

    st.markdown("---")

    # SLA Alert Banner if Breached or At Risk
    at_risk_count = len(df_req[df_req["sla_status"] == "AT_RISK"]) if "sla_status" in df_req.columns else 0
    if sla_breaches > 0 or at_risk_count > 0:
        st.error(f"⚠️ **Operational SLA Alert**: {sla_breaches} request(s) BREACHED SLA (>48h) and {at_risk_count} request(s) are AT RISK (<12h remaining). Please check the Ticket Desk queue.")

    # Charts Row 1
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📌 Requests by Status")
        status_counts = df_req["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        
        fig_status = px.pie(
            status_counts,
            names="Status",
            values="Count",
            hole=0.45,
            color="Status",
            color_discrete_map={
                "EXECUTED": "#10b981",
                "APPROVED": "#059669",
                "IN_PROGRESS": "#3b82f6",
                "DRAFT": "#6b7280",
                "REJECTED": "#ef4444",
                "SENT_BACK": "#f59e0b"
            }
        )
        fig_status.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10),
            height=280
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with c2:
        st.subheader("💳 Requests by Payment Method")
        pm_counts = df_req["payment_method"].value_counts().reset_index()
        pm_counts.columns = ["Payment Method", "Count"]

        fig_pm = px.bar(
            pm_counts,
            x="Payment Method",
            y="Count",
            color="Payment Method",
            text="Count",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pm.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=False,
            height=280
        )
        st.plotly_chart(fig_pm, use_container_width=True)

    st.markdown("---")

    # Charts Row 2
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("🛡️ Risk Distribution")
        risk_counts = df_req["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["Risk Level", "Count"]

        fig_risk = px.bar(
            risk_counts,
            x="Risk Level",
            y="Count",
            color="Risk Level",
            text="Count",
            color_discrete_map={
                "LOW RISK": "#10b981",
                "MEDIUM RISK": "#f59e0b",
                "HIGH RISK": "#ef4444",
                "CRITICAL": "#dc2626"
            }
        )
        fig_risk.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=False,
            height=280
        )
        st.plotly_chart(fig_risk, use_container_width=True)

    with c4:
        st.subheader("🏢 Requests by Merchant Tier")
        tier_counts = df_req["merchant_tier"].value_counts().reset_index()
        tier_counts.columns = ["Merchant Tier", "Count"]

        fig_tier = px.pie(
            tier_counts,
            names="Merchant Tier",
            values="Count",
            color="Merchant Tier",
            color_discrete_sequence=["#6366f1", "#8b5cf6", "#ec4899"]
        )
        fig_tier.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10),
            height=280
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    st.markdown("---")

    # Recent Active Queue Preview Table
    st.subheader("📋 Recent High-Priority Pricing Requests Queue")
    recent = df_req[df_req["status"].isin(["IN_PROGRESS", "APPROVED"])].head(6)

    if not recent.empty:
        table_data = []
        for _, r in recent.iterrows():
            table_data.append({
                "Request ID": r["request_id"],
                "Merchant": r["merchant_name"],
                "Payment Method": r["payment_method"],
                "Current MDR": f"{r['current_mdr']}%",
                "Proposed MDR": f"{r['proposed_mdr']}%",
                "Current Stage": r["current_stage"],
                "Risk": r["risk_level"],
                "SLA Status": r.get("sla_status", "UNKNOWN")
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    else:
        st.info("No active pricing requests currently in review.")
