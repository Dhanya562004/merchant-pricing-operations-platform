"""
Operational Reports Page for Merchant Pricing Operations Platform.
Generates tabular operational summaries and downloadable CSV data exports.
"""
import streamlit as st
import pandas as pd
from src.reporting import (
    generate_pricing_requests_report,
    generate_merchant_pricing_report,
    generate_margin_impact_report,
    generate_approval_history_report,
    generate_sla_performance_report,
    generate_audit_log_report,
    convert_df_to_csv
)


def render_reports():
    st.markdown("## 📈 Operational Reports & Data Downloads")
    st.caption("Export full operational datasets in CSV format for compliance, audit, and finance reconciliation.")

    report_type = st.selectbox(
        "Select Operational Report",
        [
            "Pricing Revamp Requests Report",
            "Active Merchant Pricing Configurations Report",
            "Margin & Profitability Impact Report",
            "Approval Decision History Report",
            "SLA Performance & Ticket Report",
            "Audit Trail Event Log Report"
        ]
    )

    df_report = pd.DataFrame()
    file_name = "report.csv"

    if report_type == "Pricing Revamp Requests Report":
        df_report = generate_pricing_requests_report()
        file_name = "pricing_requests_report.csv"
    elif report_type == "Active Merchant Pricing Configurations Report":
        df_report = generate_merchant_pricing_report()
        file_name = "active_merchant_pricing_report.csv"
    elif report_type == "Margin & Profitability Impact Report":
        df_report = generate_margin_impact_report()
        file_name = "margin_impact_report.csv"
    elif report_type == "Approval Decision History Report":
        df_report = generate_approval_history_report()
        file_name = "approval_history_report.csv"
    elif report_type == "SLA Performance & Ticket Report":
        df_report = generate_sla_performance_report()
        file_name = "sla_performance_report.csv"
    elif report_type == "Audit Trail Event Log Report":
        df_report = generate_audit_log_report()
        file_name = "audit_trail_report.csv"

    if df_report.empty:
        st.warning("No data available for the selected report.")
    else:
        st.markdown(f"### Report Preview ({len(df_report)} rows)")
        st.dataframe(df_report, use_container_width=True)

        csv_bytes = convert_df_to_csv(df_report)
        st.download_button(
            label=f"📥 Download {report_type} (CSV)",
            data=csv_bytes,
            file_name=file_name,
            mime="text/csv",
            type="primary"
        )


if __name__ == "__main__":
    from src.database import init_db
    from src.utils import inject_custom_css, render_sidebar_role_selector
    init_db()
    inject_custom_css()
    render_sidebar_role_selector()
    render_reports()

