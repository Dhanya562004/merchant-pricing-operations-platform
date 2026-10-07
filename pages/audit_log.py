"""
Audit Trail Explorer Page for Merchant Pricing Operations Platform.
Provides immutable audit log inspection, security tracking, and change governance history.
"""
import streamlit as st
import pandas as pd
from src.audit_engine import get_audit_logs


def render_audit_log():
    st.markdown("## 📜 Immutable Audit Trail Explorer")
    st.caption("Complete operational governance history: every pricing creation, validation, approval, ticket update, and execution event.")

    c1, c2, c3 = st.columns(3)
    with c1:
        action_f = st.selectbox("Filter by Action", [
            "ALL", "REQUEST_CREATED", "REQUEST_SUBMITTED", "VALIDATION_COMPLETED",
            "POC_APPROVED", "BANKING_APPROVED", "CHECKER_APPROVED", "FUNCTION_HEAD_APPROVED",
            "REQUEST_REJECTED", "REQUEST_SENT_BACK", "PRICING_EXECUTED", "TICKET_CREATED", "TICKET_UPDATED"
        ])
    with c2:
        search_req = st.text_input("Filter Request ID / Merchant ID", value="")
    with c3:
        record_limit = st.slider("Record Limit", min_value=50, max_value=500, value=200, step=50)

    logs = get_audit_logs(
        action_filter=action_f,
        limit=record_limit
    )

    if search_query := search_req.strip().lower():
        logs = [l for l in logs if (l["request_id"] and search_query in l["request_id"].lower()) or (l["merchant_id"] and search_query in l["merchant_id"].lower())]

    st.markdown(f"**Showing {len(logs)} audit record(s)**")

    if not logs:
        st.info("No audit records found matching criteria.")
    else:
        disp_logs = []
        for l in logs:
            disp_logs.append({
                "Event ID": l["event_id"],
                "Timestamp": l["timestamp"],
                "Action": l["action"],
                "Request ID": l["request_id"] or "N/A",
                "Merchant ID": l["merchant_id"] or "N/A",
                "Actor": l["actor"],
                "Role": l["actor_role"],
                "Old Value": l["old_value"] or "—",
                "New Value": l["new_value"] or "—",
                "Reason / Details": l["reason"] or "—"
            })
        st.dataframe(pd.DataFrame(disp_logs), use_container_width=True)


if __name__ == "__main__":
    from src.database import init_db
    from src.utils import inject_custom_css, render_sidebar_role_selector
    init_db()
    inject_custom_css()
    render_sidebar_role_selector()
    render_audit_log()

