"""
Ticket Desk & Service Workflow Page for Merchant Pricing Operations Platform.
Simulates internal ticketing system (Salesforce / Freshdesk model) for operational task routing.
"""
import streamlit as st
import pandas as pd
from src.ticket_engine import get_all_tickets, get_ticket_by_id, create_ticket, add_ticket_comment, update_ticket_status, TEAMS, PRIORITIES, CATEGORIES, STATUSES
from src.workflow_engine import get_all_requests
from src.utils import get_status_badge, get_sla_badge


def render_tickets(current_role: str):
    st.markdown("## 🎫 Ticket Desk & Operational Service Workflow")
    st.caption("Salesforce / Freshdesk-style operations ticketing, SLA monitoring, and cross-functional task routing.")

    tab1, tab2 = st.tabs(["📋 Ticket Queue & Case Management", "➕ Create Operational Ticket"])

    with tab1:
        f1, f2, f3 = st.columns(3)
        with f1:
            status_f = st.selectbox("Ticket Status", ["ALL"] + STATUSES, index=0, key="tkt_stat")
        with f2:
            team_f = st.selectbox("Assigned Team", ["ALL"] + TEAMS, index=0, key="tkt_team")
        with f3:
            prio_f = st.selectbox("Priority", ["ALL"] + PRIORITIES, index=0, key="tkt_prio")

        tickets = get_all_tickets(status_filter=status_f, team_filter=team_f, priority_filter=prio_f)

        st.markdown(f"**Found {len(tickets)} ticket(s)**")

        if not tickets:
            st.info("No tickets match the selected filters.")
        else:
            t_rows = []
            for t in tickets:
                t_rows.append({
                    "Ticket ID": t["ticket_id"],
                    "Request ID": t["request_id"],
                    "Merchant Name": t.get("merchant_name", "N/A"),
                    "Assigned Team": t["assigned_team"],
                    "Priority": t["priority"],
                    "Category": t["category"],
                    "Status": t["status"],
                    "SLA Status": t["sla_status"],
                    "Created": t["created_at"]
                })
            st.dataframe(pd.DataFrame(t_rows), use_container_width=True)

            st.markdown("---")
            st.markdown("### 🔎 Ticket Case Inspector & Discussion Timeline")

            tkt_options = {f"{t['ticket_id']} — [{t['priority']}] {t['category']} ({t['assigned_team']})": t["ticket_id"] for t in tickets}
            sel_tkt_str = st.selectbox("Select Ticket to Manage", list(tkt_options.keys()))
            sel_tkt_id = tkt_options[sel_tkt_str]

            tkt = get_ticket_by_id(sel_tkt_id)
            if tkt:
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**Ticket ID:** `{tkt['ticket_id']}`")
                c2.markdown(f"**Request ID:** `{tkt['request_id']}`")
                c3.markdown(f"**Assigned Team:** `{tkt['assigned_team']}`")
                c4.markdown(f"**Priority:** `{tkt['priority']}`")

                st.markdown(f"**Category:** {tkt['category']} | **SLA Countdown:** {tkt['time_remaining']}")

                # Discussion Thread
                st.markdown("#### 💬 Case Activity & Comment History")
                for c in tkt.get("comments_list", []):
                    with st.chat_message("user" if c.get("role") != "System" else "assistant"):
                        st.write(f"**{c.get('author', 'User')}** ({c.get('role', 'Ops')}) — *{c.get('timestamp', '')}*")
                        st.write(c.get("message", ""))

                # Add Comment & Update Status Form
                col_com, col_stat = st.columns(2)

                with col_com:
                    st.markdown("##### ✏️ Add Comment to Ticket")
                    with st.form(f"add_com_form_{tkt['ticket_id']}"):
                        com_author = st.text_input("Your Name", value=f"{current_role} User")
                        com_msg = st.text_area("Comment Message", placeholder="Type case update or query...")
                        btn_com = st.form_submit_button("Post Comment")

                        if btn_com and com_msg.strip():
                            add_ticket_comment(sel_tkt_id, com_author, current_role, com_msg)
                            st.success("Comment added!")
                            st.rerun()

                with col_stat:
                    st.markdown("##### ⚙️ Update Ticket Status / Team")
                    with st.form(f"upd_stat_form_{tkt['ticket_id']}"):
                        new_st = st.selectbox("New Status", STATUSES, index=STATUSES.index(tkt["status"]) if tkt["status"] in STATUSES else 0)
                        new_team = st.selectbox("Reassign Team", TEAMS, index=TEAMS.index(tkt["assigned_team"]) if tkt["assigned_team"] in TEAMS else 0)
                        res_notes = st.text_area("Resolution Notes", value=tkt.get("resolution", ""))
                        btn_upd = st.form_submit_button("Update Case Status")

                        if btn_upd:
                            update_ticket_status(
                                ticket_id=sel_tkt_id,
                                new_status=new_st,
                                assigned_team=new_team,
                                resolution=res_notes,
                                updater=f"{current_role} User",
                                updater_role=current_role
                            )
                            st.success("Ticket updated successfully!")
                            st.rerun()

    with tab2:
        st.markdown("### ➕ Create Operational Ticket")
        reqs = get_all_requests()
        req_opts = {f"{r['request_id']} — {r['merchant_name']}": (r["request_id"], r["merchant_id"]) for r in reqs} if reqs else {}

        if not req_opts:
            st.warning("No pricing requests available to attach ticket to.")
        else:
            with st.form("create_ticket_form"):
                sel_req_label = st.selectbox("Select Associated Request", list(req_opts.keys()))
                req_id, merch_id = req_opts[sel_req_label]

                t1, t2 = st.columns(2)
                with t1:
                    assigned_team = st.selectbox("Assign to Team", TEAMS)
                    priority = st.selectbox("Priority Level", PRIORITIES, index=1)
                with t2:
                    category = st.selectbox("Category", CATEGORIES)
                    creator = st.text_input("Creator Name", value=f"{current_role} User")

                initial_desc = st.text_area("Ticket Description / Instructions", placeholder="Explain the operational issue or missing document requirement...", height=100)

                sub_tkt = st.form_submit_button("🎟️ Create Operational Ticket")

                if sub_tkt:
                    if not initial_desc.strip():
                        st.error("Please enter a ticket description.")
                    else:
                        new_t = create_ticket(
                            request_id=req_id,
                            merchant_id=merch_id,
                            assigned_team=assigned_team,
                            priority=priority,
                            category=category,
                            initial_comment=initial_desc,
                            creator=creator,
                            creator_role=current_role
                        )
                        st.success(f"🎉 Ticket **{new_t['ticket_id']}** created and assigned to **{assigned_team}**!")
                        st.rerun()


if __name__ == "__main__":
    from src.database import init_db
    from src.utils import inject_custom_css, render_sidebar_role_selector
    init_db()
    inject_custom_css()
    role = render_sidebar_role_selector()
    render_tickets(role)

