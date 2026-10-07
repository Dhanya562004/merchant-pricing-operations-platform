"""
Merchant Pricing Configuration Page for Merchant Pricing Operations Platform.
Displays active master pricing matrix across payment methods with comparative side-by-side view.
"""
import streamlit as st
import pandas as pd
from src.pricing_engine import get_all_active_pricing, get_all_merchants, get_merchant_all_pricing
from src.utils import format_inr, format_pct


def render_pricing_configuration():
    st.markdown("## ⚙️ Merchant Pricing Configuration Master Data")
    st.caption("Active operational rate cards across payment methods: Cards, UPI Recurring, E-Mandate, and Optimiser.")

    pricing_list = get_all_active_pricing()
    merchants = get_all_merchants()

    if not pricing_list:
        st.warning("No active pricing configuration records found.")
        return

    df_p = pd.DataFrame(pricing_list)

    tab1, tab2 = st.tabs(["📊 Active Master Pricing Matrix", "🔎 Single Merchant Pricing Profile"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            pm_filter = st.selectbox("Filter Payment Method", ["ALL", "Cards", "UPI Recurring", "E-Mandate", "Optimiser"], key="cfg_pm")
        with c2:
            tier_filter = st.selectbox("Filter Merchant Tier", ["ALL", "Enterprise", "Mid-Market", "SMB"], key="cfg_tier")
        with c3:
            search_merchant = st.text_input("Search Merchant Name", key="cfg_search")

        filtered_df = df_p.copy()
        if pm_filter != "ALL":
            filtered_df = filtered_df[filtered_df["payment_method"] == pm_filter]
        if tier_filter != "ALL":
            filtered_df = filtered_df[filtered_df["merchant_tier"] == tier_filter]
        if search_merchant.strip():
            sq = search_merchant.strip().lower()
            filtered_df = filtered_df[filtered_df["merchant_name"].str.lower().str.contains(sq)]

        st.markdown(f"**Showing {len(filtered_df)} configured rate card(s)**")

        disp_df = filtered_df[[
            "merchant_id", "merchant_name", "merchant_tier", "industry",
            "payment_method", "mdr_percent", "fixed_fee", "minimum_fee",
            "maximum_fee", "effective_from", "pricing_status", "last_updated_by"
        ]].rename(columns={
            "merchant_id": "Merchant ID",
            "merchant_name": "Merchant Name",
            "merchant_tier": "Tier",
            "industry": "Industry",
            "payment_method": "Payment Method",
            "mdr_percent": "MDR %",
            "fixed_fee": "Fixed Fee (₹)",
            "minimum_fee": "Min Fee",
            "maximum_fee": "Max Fee",
            "effective_from": "Effective From",
            "pricing_status": "Status",
            "last_updated_by": "Updated By"
        })

        st.dataframe(disp_df, use_container_width=True)

    with tab2:
        m_options = {f"{m['merchant_name']} ({m['merchant_id']})": m["merchant_id"] for m in merchants}
        sel_m_label = st.selectbox("Select Merchant Profile", list(m_options.keys()))
        sel_m_id = m_options[sel_m_label]

        m_info = next((m for m in merchants if m["merchant_id"] == sel_m_id), None)
        if m_info:
            i1, i2, i3, i4 = st.columns(4)
            i1.metric("Industry", m_info["industry"])
            i2.metric("Tier", m_info["merchant_tier"])
            i3.metric("Monthly GMV", format_inr(m_info["monthly_gmv"]))
            i4.metric("Risk Category", m_info["risk_category"])

            st.markdown("#### Configured Rate Cards Across Payment Methods")
            m_pricing = get_merchant_all_pricing(sel_m_id)

            if m_pricing:
                p_rows = []
                for p in m_pricing:
                    p_rows.append({
                        "Payment Method": p["payment_method"],
                        "MDR (%)": f"{p['mdr_percent']}%",
                        "Fixed Fee (₹)": f"₹{p['fixed_fee']}",
                        "Min Fee": f"₹{p['minimum_fee']}",
                        "Max Fee": f"₹{p['maximum_fee']}",
                        "Effective From": p["effective_from"],
                        "Status": p["pricing_status"],
                        "Last Updated By": p["last_updated_by"]
                    })
                st.dataframe(pd.DataFrame(p_rows), use_container_width=True)
            else:
                st.info("No active pricing configured for this merchant.")


if __name__ == "__main__":
    from src.database import init_db
    from src.utils import inject_custom_css, render_sidebar_role_selector
    init_db()
    inject_custom_css()
    render_sidebar_role_selector()
    render_pricing_configuration()

