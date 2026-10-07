"""
Approval Hierarchy Workbench Page for Merchant Pricing Operations Platform.
Handles stage-by-stage multi-level approval reviews, role gating, and execution triggers.
"""
import streamlit as st
import pandas as pd
from src.workflow_engine import get_all_requests, get_request_by_id, execute_pricing_change
from src.approval_engine import process_approval_decision, get_approval_history, can_role_approve_stage
from src.utils import format_inr, format_pct, get_status_badge, get_risk_badge, get_sla_badge


def render_approvals(current_role: str):
    st.markdown("## ✅ Multi-Level Approval Hierarchy Workbench")
    st.caption("Stage-by-stage approval reviews, role-authorized decision making, and pricing execution triggers.")

    st.info(f"👤 **Current Demo Role:** `{current_role}`. Actions on approval stages are strictly governed by role permissions.")

    all_reqs = get_all_requests()
    pending = [r for r in all_reqs if r["status"] in ["IN_PROGRESS", "APPROVED"] and r["current_stage"] != "EXECUTED"]

    tab1, tab2, tab3 = st.tabs(["⏳ Pending Approval Queue", "⚡ Ready for Execution", "📜 Approval Decision History"])

    with tab1:
        if not pending:
            st.success("🎉 No pending pricing revamp requests requiring approval at this time.")
        else:
            req_options = {f"[{r['current_stage']}] {r['request_id']} — {r['merchant_name']} ({r['payment_method']})" : r["request_id"] for r in pending if r["current_stage"] != "READY_FOR_EXECUTION"}

            if not req_options:
                st.info("No requests currently pending stage review.")
            else:
                sel_label = st.selectbox("Select Request to Review", list(req_options.keys()))
                sel_req_id = req_options[sel_label]
                req = get_request_by_id(sel_req_id)

                if req:
                    stage = req["current_stage"]
                    st.markdown(f"### Reviewing Request: `{req['request_id']}`")

                    # Stage & Authorization Header
                    is_authorized = can_role_approve_stage(current_role, stage)
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(f"**Current Stage:** `{stage}`")
                    c2.markdown(f"**Risk Classification:** {req['risk_level']}")
                    c3.markdown(f"**Required Approval:** `{req['required_approval_level']}`")
                    c4.markdown(f"**Authorization:** {'🟢 AUTHORIZED' if is_authorized else '🔴 ROLE NOT AUTHORIZED'}")

                    if not is_authorized:
                        st.warning(f"🔒 **Role Lock:** Your active Demo Role **'{current_role}'** is not authorized to approve stage **'{stage}'**. Switch Demo Role in the sidebar to test approval.")

                    st.markdown("---")
                    # Overview Cards
                    v1, v2, v3, v4 = st.columns(4)
                    v1.metric("Current MDR", f"{req['current_mdr']}%")
                    v2.metric("Proposed MDR", f"{req['proposed_mdr']}%", delta=f"{req['proposed_mdr'] - req['current_mdr']:.2f}%", delta_color="inverse")
                    v3.metric("Current Fixed Fee", f"₹{req['current_fixed_fee']}")
                    v4.metric("Proposed Fixed Fee", f"₹{req['proposed_fixed_fee']}", delta=f"₹{req['proposed_fixed_fee'] - req['current_fixed_fee']:.2f}", delta_color="inverse")

                    st.markdown(f"**Business Justification:** {req['business_justification']}")
                    st.markdown(f"**Reason for Change:** {req['reason']}")

                    # Approval Decision Form
                    st.markdown("#### 📝 Record Approval Decision")
                    with st.form("approval_action_form"):
                        reviewer_name = st.text_input("Reviewer Name", value=f"{current_role} User")
                        decision = st.radio("Decision", ["APPROVE", "REJECT", "SEND BACK"], horizontal=True)
                        comments = st.text_area("Reviewer Comments (Mandatory)", placeholder="Enter detailed operational rationale or conditions for decision...", height=80)
                        reason_code = st.selectbox("Reason Category", [
                            "Met Tier GMV Requirements",
                            "Competitive Churn Defense",
                            "Margin Profitability Standard Satisfied",
                            "Executive / Strategy Approval Granted",
                            "Incomplete Risk Clearance",
                            "Negative Margin Policy Violation",
                            "Unjustified Price Cut"
                        ])

                        submit_btn = st.form_submit_button("Submit Approval Decision", disabled=not is_authorized)

                        if submit_btn:
                            if not comments.strip() or len(comments.strip()) < 5:
                                st.error("Please enter mandatory reviewer comments (at least 5 characters).")
                            else:
                                try:
                                    updated_req = process_approval_decision(
                                        request_id=sel_req_id,
                                        reviewer=reviewer_name,
                                        reviewer_role=current_role,
                                        decision=decision,
                                        comments=comments,
                                        reason=reason_code
                                    )
                                    st.success(f"✅ Approval decision **{decision}** recorded successfully! Request stage updated to `{updated_req['current_stage']}`.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error processing decision: {str(e)}")

    with tab2:
        st.markdown("### ⚡ Approved Requests Ready for Pricing Execution")
        ready_reqs = [r for r in all_reqs if r["current_stage"] == "READY_FOR_EXECUTION" or r["status"] == "APPROVED"]

        if not ready_reqs:
            st.info("No approved requests currently waiting for execution.")
        else:
            for req in ready_reqs:
                with st.expander(f"🚀 `{req['request_id']}` — {req['merchant_name']} ({req['payment_method']})", expanded=True):
                    e1, e2, e3, e4 = st.columns(4)
                    e1.markdown(f"**Current Rate:** {req['current_mdr']}% + ₹{req['current_fixed_fee']}")
                    e2.markdown(f"**Proposed Rate:** {req['proposed_mdr']}% + ₹{req['proposed_fixed_fee']}")
                    e3.markdown(f"**Effective Date:** {req['effective_date']}")
                    e4.markdown(f"**Risk Level:** {req['risk_level']}")

                    if st.button(f"⚡ Execute Pricing Change in Production (`{req['request_id']}`)", key=f"exec_{req['request_id']}"):
                        try:
                            exec_res = execute_pricing_change(
                                request_id=req["request_id"],
                                executor=f"{current_role} User",
                                executor_role=current_role
                            )
                            st.success(f"🎉 Pricing change for **{req['merchant_name']}** has been EXECUTED in production configuration! Status: `{exec_res['status']}`")
                            st.balloons()
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Execution Error: {str(e)}")

    with tab3:
        st.markdown("### 📜 Global Approval Decision Log")
        all_history = []
        for r in all_reqs:
            hist = get_approval_history(r["request_id"])
            all_history.extend(hist)

        if all_history:
            st.dataframe(pd.DataFrame(all_history), use_container_width=True)
        else:
            st.info("No approval logs recorded.")


if __name__ == "__main__":
    from src.database import init_db
    from src.utils import inject_custom_css, render_sidebar_role_selector
    init_db()
    inject_custom_css()
    role = render_sidebar_role_selector()
    render_approvals(role)

