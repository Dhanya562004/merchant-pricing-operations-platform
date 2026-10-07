"""
Admin & Policy Settings Page for Merchant Pricing Operations Platform.
Allows Operations Admin to configure business policy thresholds and reset demo data.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from src.database import get_connection, reset_database
from src.audit_engine import log_audit_event


def render_admin_settings(current_role: str):
    st.markdown("## ⚙️ Admin & Policy Governance Settings")
    st.caption("Configure operational policy thresholds, approval routing limits, and reset demo datasets.")

    if current_role != "Operations Admin":
        st.warning(f"⚠️ Your active Demo Role is **'{current_role}'**. Policy configuration edits require **Operations Admin** role.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policy_config ORDER BY policy_key ASC")
    policies = [dict(r) for r in cursor.fetchall()]
    conn.close()

    st.markdown("### 📋 Active Business Policy Rules")

    with st.form("policy_update_form"):
        updated_vals = {}
        for p in policies:
            pkey = p["policy_key"]
            pname = p["policy_name"]
            pval = float(p["value"])
            pdesc = p["description"]

            st.markdown(f"**{pname}** (`{pkey}`)")
            st.caption(pdesc)
            val_input = st.number_input(f"Value for {pname}", value=pval, step=1.0 if pval > 10 else 0.5, key=f"pol_{pkey}")
            updated_vals[pkey] = val_input
            st.markdown("---")

        save_pol_btn = st.form_submit_button("💾 Save Updated Policy Thresholds", disabled=(current_role != "Operations Admin"))

        if save_pol_btn:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = get_connection()
            cursor = conn.cursor()
            for pk, pv in updated_vals.items():
                cursor.execute("UPDATE policy_config SET value = ?, updated_at = ? WHERE policy_key = ?", (pv, now_str, pk))
            conn.commit()
            conn.close()

            log_audit_event(
                request_id=None,
                merchant_id=None,
                actor=f"{current_role} User",
                actor_role=current_role,
                action="POLICY_UPDATED",
                old_value="Previous thresholds",
                new_value=str(updated_vals),
                reason="Admin policy thresholds update"
            )
            st.success("Business policy thresholds updated successfully!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔄 Reset Demo Dataset")
    st.caption("Reset SQLite database to original pre-seeded demo state (14 merchants, 22 pricing requests, active tickets, full audit trail).")

    if st.button("🚨 Reset All Demo Data", type="secondary"):
        reset_database()
        st.success("🎉 Database reset to original demo state successfully!")
        st.rerun()
