"""
Pricing Request Workbench Page for Merchant Pricing Operations Platform.
Provides request queue management, live validation engine test, and request submission form.
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime
from src.pricing_engine import get_all_merchants, get_active_pricing, compare_pricing
from src.workflow_engine import get_all_requests, create_pricing_request, get_request_by_id
from src.validation_engine import validate_pricing_request
from src.margin_engine import calculate_financial_impact, get_banking_costs_for_request
from src.approval_engine import get_approval_history
from src.utils import format_inr, format_pct, get_status_badge, get_risk_badge, get_sla_badge


def render_pricing_requests(current_role: str):
    st.markdown("## 📋 Pricing Revamp Request Workbench")
    st.caption("Manage merchant pricing change requests, execute validation checks, and submit new revamp proposals.")

    tab1, tab2 = st.tabs(["🔍 Request Queue & Details", "➕ Create New Pricing Revamp Request"])

    # ==========================================
    # TAB 1: REQUEST QUEUE & DETAIL VIEW
    # ==========================================
    with tab1:
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            status_filter = st.selectbox("Status Filter", ["ALL", "IN_PROGRESS", "APPROVED", "EXECUTED", "REJECTED", "SENT_BACK", "DRAFT"], index=0)
        with f2:
            pm_filter = st.selectbox("Payment Method", ["ALL", "Cards", "UPI Recurring", "E-Mandate", "Optimiser"], index=0)
        with f3:
            risk_filter = st.selectbox("Risk Level", ["ALL", "LOW RISK", "MEDIUM RISK", "HIGH RISK", "CRITICAL"], index=0)
        with f4:
            search_query = st.text_input("Search (Merchant / Request ID)", value="")

        requests = get_all_requests(
            status_filter=status_filter,
            payment_filter=pm_filter,
            risk_filter=risk_filter
        )

        if search_query.strip():
            sq = search_query.strip().lower()
            requests = [r for r in requests if sq in r["request_id"].lower() or sq in r["merchant_name"].lower()]

        st.markdown(f"**Found {len(requests)} pricing request(s)**")

        if not requests:
            st.info("No matching pricing requests found.")
        else:
            # Table View
            table_rows = []
            for r in requests:
                table_rows.append({
                    "Request ID": r["request_id"],
                    "Merchant Name": r["merchant_name"],
                    "Tier": r["merchant_tier"],
                    "Payment Method": r["payment_method"],
                    "Current MDR": f"{r['current_mdr']}%",
                    "Proposed MDR": f"{r['proposed_mdr']}%",
                    "Current Fixed": f"₹{r['current_fixed_fee']}",
                    "Proposed Fixed": f"₹{r['proposed_fixed_fee']}",
                    "Current Stage": r["current_stage"],
                    "Status": r["status"],
                    "Risk": r["risk_level"],
                    "Required Approval": r["required_approval_level"],
                    "SLA": r["time_remaining_str"]
                })

            df_disp = pd.DataFrame(table_rows)
            st.dataframe(df_disp, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🔎 Request Detail & Approval Audit Explorer")

            req_options = [f"{r['request_id']} — {r['merchant_name']} ({r['payment_method']})" for r in requests]
            selected_req_str = st.selectbox("Select Request to View Details", req_options)

            if selected_req_str:
                sel_req_id = selected_req_str.split(" — ")[0]
                req = get_request_by_id(sel_req_id)

                if req:
                    st.markdown(f"### Request Summary: `{req['request_id']}`")
                    
                    d1, d2, d3, d4 = st.columns(4)
                    d1.markdown(f"**Merchant:** {req['merchant_name']} ({req['merchant_tier']})")
                    d2.markdown(f"**Payment Method:** {req['payment_method']}")
                    d3.markdown(f"**Current Stage:** `{req['current_stage']}`")
                    d4.markdown(f"**Status:** {req['status']}")

                    r1, r2, r3, r4 = st.columns(4)
                    r1.markdown(f"**Risk Level:** {req['risk_level']}")
                    r2.markdown(f"**Approval Req:** `{req['required_approval_level']}`")
                    r3.markdown(f"**Requestor:** {req['requestor']}")
                    r4.markdown(f"**SLA:** {req['time_remaining_str']}")

                    st.markdown("#### 💰 Price & Revenue Comparison")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Current MDR", f"{req['current_mdr']}%")
                    c2.metric("Proposed MDR", f"{req['proposed_mdr']}%", delta=f"{req['proposed_mdr'] - req['current_mdr']:.2f}%", delta_color="inverse")
                    c3.metric("Current Fixed Fee", f"₹{req['current_fixed_fee']}")
                    c4.metric("Proposed Fixed Fee", f"₹{req['proposed_fixed_fee']}", delta=f"₹{req['proposed_fixed_fee'] - req['current_fixed_fee']:.2f}", delta_color="inverse")

                    # Business Justification & Notes
                    st.markdown("#### 📝 Business Justification & Reason")
                    st.info(f"**Reason:** {req['reason']}\n\n**Justification:** {req['business_justification']}\n\n**Supporting Notes:** {req['supporting_notes'] or 'None'}")

                    # Validation Check Results
                    st.markdown("#### 🛡️ Deterministic Validation Engine Results")
                    val_res = validate_pricing_request(
                        merchant_id=req["merchant_id"],
                        payment_method=req["payment_method"],
                        current_mdr=req["current_mdr"],
                        proposed_mdr=req["proposed_mdr"],
                        current_fixed_fee=req["current_fixed_fee"],
                        proposed_fixed_fee=req["proposed_fixed_fee"],
                        effective_date_str=req["effective_date"],
                        reason=req["reason"],
                        business_justification=req["business_justification"],
                        expected_monthly_gmv=req["expected_monthly_gmv"],
                        request_id=req["request_id"]
                    )

                    st.markdown(f"**Validation Status:** `{val_res['overall_status']}` | Summary: {val_res['summary']}")

                    with st.expander("Show Detailed Validation Rules Checked", expanded=False):
                        for rule in val_res["rules_checked"]:
                            res_color = "🟢" if rule["result"] == "PASS" else ("🟡" if rule["result"] == "WARNING" else "🔴")
                            st.write(f"{res_color} **{rule['rule']}** [{rule['severity']}] — *{rule['explanation']}*")

                    # Approval History Timeline
                    st.markdown("#### ⏳ Approval History Timeline")
                    history = get_approval_history(req["request_id"])
                    if history:
                        hist_rows = []
                        for h in history:
                            hist_rows.append({
                                "Stage": h["stage"],
                                "Reviewer": h["reviewer"],
                                "Role": h["role"],
                                "Decision": h["decision"],
                                "Comments": h["comments"],
                                "Reason": h["reason"],
                                "Timestamp": h["created_at"]
                            })
                        st.dataframe(pd.DataFrame(hist_rows), use_container_width=True)
                    else:
                        st.caption("No approval decisions recorded yet.")

    # ==========================================
    # TAB 2: CREATE NEW PRICING REVAMP REQUEST
    # ==========================================
    with tab2:
        st.markdown("### ➕ Create Pricing Revamp Request")
        
        # Role Gate check
        if current_role not in ["Pricing Analyst", "Operations Admin"]:
            st.warning(f"⚠️ Your current Demo Role is **'{current_role}'**. Pricing revamp requests can typically only be created by **Pricing Analyst** or **Operations Admin**.")

        merchants = get_all_merchants()
        if not merchants:
            st.warning("No merchants found in database.")
            return

        m_options = {f"{m['merchant_name']} ({m['merchant_id']}) — {m['merchant_tier']}": m["merchant_id"] for m in merchants}
        
        with st.form("create_request_form"):
            col_a, col_b = st.columns(2)

            with col_a:
                selected_m_label = st.selectbox("Select Merchant", list(m_options.keys()))
                sel_merchant_id = m_options[selected_m_label]
                
                payment_method = st.selectbox("Payment Method", ["Cards", "UPI Recurring", "E-Mandate", "Optimiser"])

                # Fetch active pricing for auto-population
                active_p = get_active_pricing(sel_merchant_id, payment_method)
                curr_mdr = float(active_p["mdr_percent"]) if active_p else 1.85
                curr_fixed = float(active_p["fixed_fee"]) if active_p else 0.0

                st.markdown(f"**Current Configured MDR:** `{curr_mdr}%` | **Current Fixed Fee:** `₹{curr_fixed}`")

                proposed_mdr = st.number_input("Proposed MDR (%)", min_value=0.0, max_value=5.0, value=max(0.0, curr_mdr - 0.20), step=0.05, format="%.2f")
                proposed_fixed = st.number_input("Proposed Fixed Fee (₹)", min_value=0.0, max_value=500.0, value=curr_fixed, step=0.5, format="%.2f")

            with col_b:
                effective_date = st.date_input("Effective Date", value=date.today())
                
                # Fetch default GMV
                m_details = next((m for m in merchants if m["merchant_id"] == sel_merchant_id), None)
                def_gmv = float(m_details["monthly_gmv"]) if m_details else 10000000.0

                expected_gmv = st.number_input("Expected Monthly GMV (₹)", min_value=1000.0, value=def_gmv, step=1000000.0, format="%.0f")

                reason = st.text_input("Reason for Pricing Change", placeholder="e.g. Competitive match against Razorpay bid / Volume upgrade")
                requestor = st.text_input("Requestor Name", value=f"{current_role} User")

            business_justification = st.text_area("Business Justification (Mandatory)", placeholder="Detailed justification explaining volume growth, market defense, or strategic relationship...", height=100)
            supporting_notes = st.text_area("Supporting Notes / Rate Card Attachments (Optional)", placeholder="Interchange assumptions, competitor comparison notes...", height=70)

            st.markdown("#### ⚡ Real-Time Pre-Submission Validation Preview")

            # Run real-time validation preview
            val_preview = validate_pricing_request(
                merchant_id=sel_merchant_id,
                payment_method=payment_method,
                current_mdr=curr_mdr,
                proposed_mdr=proposed_mdr,
                current_fixed_fee=curr_fixed,
                proposed_fixed_fee=proposed_fixed,
                effective_date_str=str(effective_date),
                reason=reason or "Draft",
                business_justification=business_justification or "Placeholder justification",
                expected_monthly_gmv=expected_gmv
            )

            p1, p2, p3 = st.columns(3)
            p1.markdown(f"**Predicted Validation:** `{val_preview['overall_status']}`")
            p2.markdown(f"**Predicted Risk:** {val_preview['risk_level']}")
            p3.markdown(f"**Required Approval Stage:** `{val_preview['required_approval_level']}`")

            if val_preview["overall_status"] == "BLOCKED":
                st.error(f"⛔ **Blocked Warning:** {val_preview['summary']}")
            elif val_preview["overall_status"] == "WARNING":
                st.warning(f"⚠️ **Warning Notice:** {val_preview['summary']}")

            submitted = st.form_submit_button("🚀 Submit Pricing Revamp Request")

            if submitted:
                if not reason.strip() or len(reason.strip()) < 5:
                    st.error("Please enter a valid reason for the pricing change.")
                elif not business_justification.strip() or len(business_justification.strip()) < 10:
                    st.error("Business justification must be at least 10 characters long.")
                elif val_preview["overall_status"] == "BLOCKED":
                    st.error("Cannot submit request because validation status is BLOCKED. Please revise proposed pricing parameters.")
                else:
                    new_req = create_pricing_request(
                        merchant_id=sel_merchant_id,
                        payment_method=payment_method,
                        current_mdr=curr_mdr,
                        proposed_mdr=proposed_mdr,
                        current_fixed_fee=curr_fixed,
                        proposed_fixed_fee=proposed_fixed,
                        effective_date=str(effective_date),
                        reason=reason,
                        expected_monthly_gmv=expected_gmv,
                        requestor=requestor,
                        business_justification=business_justification,
                        supporting_notes=supporting_notes
                    )
                    st.success(f"🎉 Pricing revamp request **{new_req['request_id']}** submitted successfully! Current Stage: `{new_req['current_stage']}`")
                    st.balloons()


if __name__ == "__main__":
    from src.database import init_db
    from src.utils import inject_custom_css, render_sidebar_role_selector
    init_db()
    inject_custom_css()
    role = render_sidebar_role_selector()
    render_pricing_requests(role)

