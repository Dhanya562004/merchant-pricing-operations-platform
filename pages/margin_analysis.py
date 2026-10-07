"""
Margin & Profitability Analysis Page for Merchant Pricing Operations Platform.
Provides deep-dive financial modeling, transparent calculation formulas, and banking cost card entry.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.workflow_engine import get_all_requests, get_request_by_id
from src.margin_engine import calculate_financial_impact, get_banking_costs_for_request, save_banking_costs
from src.pricing_engine import get_all_merchants
from src.utils import format_inr, format_pct, get_risk_badge


def render_margin_analysis(current_role: str):
    st.markdown("## 💰 Margin & Profitability Analysis Engine")
    st.caption("Deep-dive profitability analysis, banking network cost modeling, and gross margin calculations.")

    st.markdown("""
    > [!NOTE]  
    > **Transparent Profitability Formulas:**  
    > - $\\text{Revenue} = (\\text{GMV} \\times \\frac{\\text{MDR}}{100}) + (\\text{Tx Count} \\times \\text{Fixed Fee})$  
    > - $\\text{Total Cost} = (\\text{GMV} \\times \\frac{\\text{Network Cost} + \\text{Bank Cost}}{100}) + (\\text{Tx Count} \\times (\\text{Proc Fixed} + \\text{Ops Fixed}))$  
    > - $\\text{Gross Margin} = \\text{Revenue} - \\text{Total Cost}$  
    > - $\\text{Margin } \\% = \\frac{\\text{Gross Margin}}{\\text{Revenue}} \\times 100$
    """)

    mode = st.radio("Analysis Mode", ["Analyze Existing Pricing Request", "Interactive Custom Scenario Simulator"], horizontal=True)

    if mode == "Analyze Existing Pricing Request":
        requests = get_all_requests()
        if not requests:
            st.warning("No pricing requests found.")
            return

        req_options = {f"{r['request_id']} — {r['merchant_name']} ({r['payment_method']})": r["request_id"] for r in requests}
        sel_label = st.selectbox("Select Pricing Request to Analyze", list(req_options.keys()))
        sel_req_id = req_options[sel_label]

        req = get_request_by_id(sel_req_id)
        if not req:
            st.error("Request details not found.")
            return

        st.markdown(f"### Financial Analysis for `{req['request_id']}`")

        # Fetch or default banking costs
        b_costs = get_banking_costs_for_request(sel_req_id)
        net_cost_def = float(b_costs["network_cost_percent"]) if b_costs else 1.05
        bank_cost_def = float(b_costs["bank_cost_percent"]) if b_costs else 0.30
        proc_fixed_def = float(b_costs["processing_cost_fixed"]) if b_costs else 0.05
        other_fixed_def = float(b_costs["other_op_cost_fixed"]) if b_costs else 0.02
        b_notes_def = b_costs["notes"] if b_costs else ""

        st.markdown("#### 🏦 Banking Cost Assumptions (Banking Operations Entry)")
        with st.form("banking_cost_form"):
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                net_cost = st.number_input("Network Interchange Fee (%)", min_value=0.0, max_value=3.0, value=net_cost_def, step=0.05, format="%.2f")
            with bc2:
                bank_cost = st.number_input("Acquiring Bank Fee (%)", min_value=0.0, max_value=2.0, value=bank_cost_def, step=0.05, format="%.2f")
            with bc3:
                proc_fixed = st.number_input("Gateway Proc Fixed (₹)", min_value=0.0, max_value=10.0, value=proc_fixed_def, step=0.01, format="%.2f")
            with bc4:
                other_fixed = st.number_input("Ops & Risk Fixed (₹)", min_value=0.0, max_value=10.0, value=other_fixed_def, step=0.01, format="%.2f")

            cost_notes = st.text_input("Banking Cost Notes / Rate Card Verification", value=b_notes_def, placeholder="e.g. Verified ICICI Enterprise rate card")
            save_bc_btn = st.form_submit_button("💾 Save Banking Cost Assumptions")

            if save_bc_btn:
                save_banking_costs(
                    request_id=sel_req_id,
                    network_cost_percent=net_cost,
                    bank_cost_percent=bank_cost,
                    processing_cost_fixed=proc_fixed,
                    other_op_cost_fixed=other_fixed,
                    notes=cost_notes,
                    updated_by=current_role
                )
                st.success("Banking cost assumptions updated successfully!")

        # Calculate Financial Metrics
        gmv = float(req["expected_monthly_gmv"])
        fin = calculate_financial_impact(
            monthly_gmv=gmv,
            transaction_count=10000,
            current_mdr=float(req["current_mdr"]),
            proposed_mdr=float(req["proposed_mdr"]),
            current_fixed_fee=float(req["current_fixed_fee"]),
            proposed_fixed_fee=float(req["proposed_fixed_fee"]),
            network_cost_percent=net_cost,
            bank_cost_percent=bank_cost,
            processing_cost_fixed=proc_fixed,
            other_op_cost_fixed=other_fixed
        )

        st.markdown("#### 📈 Profitability Metrics Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Monthly Revenue", format_inr(fin["current_revenue"]))
        m2.metric("Proposed Monthly Revenue", format_inr(fin["proposed_revenue"]), delta=format_inr(fin["monthly_revenue_impact"]))
        m3.metric("Total Processing Cost", format_inr(fin["total_processing_cost"]))
        m4.metric("Projected Gross Margin %", f"{fin['projected_margin_pct']}%", delta=f"{fin['projected_margin_pct'] - fin['current_margin_pct']:.2f}%")

        st.markdown("#### 🗓️ Revenue & Margin Impact Projection")
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Monthly Revenue Impact", format_inr(fin["monthly_revenue_impact"]))
        i2.metric("Monthly Margin Impact", format_inr(fin["monthly_margin_impact"]))
        i3.metric("Annualized Revenue Impact", format_inr(fin["annualized_revenue_impact"]))
        i4.metric("Annualized Margin Impact", format_inr(fin["annualized_margin_impact"]))

        # Loss-making Warning
        if fin["is_loss_making"]:
            st.error("🚨 **CRITICAL POLICY BREACH:** Projected Gross Margin is **NEGATIVE** (Loss Making). This request is automatically BLOCKED from execution.")
        elif fin["projected_margin_pct"] < 5.0:
            st.warning("⚠️ **HIGH RISK WARNING:** Projected Gross Margin is below 5.0%. Requires Function Head Approval.")

        # Waterfall Chart
        fig_waterfall = go.Figure(go.Waterfall(
            name="Profitability Breakdown",
            orientation="v",
            measure=["relative", "relative", "total", "relative", "total"],
            x=["Proposed Revenue", "Network & Bank Costs", "Net Processing Margin", "Fixed Op Costs", "Projected Gross Margin"],
            textposition="outside",
            text=[f"₹{fin['proposed_revenue']:,.0f}", f"-₹{gmv * (fin['total_cost_percent']/100):,.0f}", "", f"-₹{10000 * fin['total_cost_fixed']:,.0f}", f"₹{fin['projected_gross_margin']:,.0f}"],
            y=[fin["proposed_revenue"], -(gmv * (fin["total_cost_percent"]/100)), 0, -(10000 * fin["total_cost_fixed"]), fin["projected_gross_margin"]],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        fig_waterfall.update_layout(
            title="Monthly Financial Waterfall Breakdown (₹)",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)

    else: # Custom Scenario Simulator
        st.markdown("### 🧪 Custom Pricing & Margin Scenario Simulator")
        col1, col2 = st.columns(2)
        with col1:
            test_gmv = st.number_input("Test Monthly GMV (₹)", value=50000000.0, step=5000000.0, format="%.0f")
            test_tx = st.number_input("Test Transaction Count", value=100000, step=10000)
            c_mdr = st.number_input("Current MDR (%)", value=2.0, step=0.1)
            p_mdr = st.number_input("Proposed MDR (%)", value=1.6, step=0.1)
        with col2:
            net_c = st.number_input("Network Cost (%)", value=1.05, step=0.05)
            bank_c = st.number_input("Bank Cost (%)", value=0.30, step=0.05)
            proc_f = st.number_input("Processing Fixed Cost (₹)", value=0.05, step=0.01)
            ops_f = st.number_input("Other Ops Fixed Cost (₹)", value=0.02, step=0.01)

        sim_fin = calculate_financial_impact(
            monthly_gmv=test_gmv,
            transaction_count=test_tx,
            current_mdr=c_mdr,
            proposed_mdr=p_mdr,
            current_fixed_fee=0.0,
            proposed_fixed_fee=0.0,
            network_cost_percent=net_c,
            bank_cost_percent=bank_c,
            processing_cost_fixed=proc_f,
            other_op_cost_fixed=ops_f
        )

        st.markdown("#### Simulation Results")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Proposed Revenue", format_inr(sim_fin["proposed_revenue"]))
        s2.metric("Total Processing Cost", format_inr(sim_fin["total_processing_cost"]))
        s3.metric("Projected Gross Margin", format_inr(sim_fin["projected_gross_margin"]))
        s4.metric("Margin %", f"{sim_fin['projected_margin_pct']}%")
