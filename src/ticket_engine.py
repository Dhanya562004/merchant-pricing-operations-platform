"""
Ticket Engine for Merchant Pricing Operations Platform.
Simulates internal ticketing / service workflow (Salesforce / Freshdesk model).
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from src.database import get_connection
from src.audit_engine import log_audit_event


TEAMS = ["Pricing Operations", "Banking Operations", "Checker Team", "Finance", "Engineering"]
PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
CATEGORIES = ["Margin Review", "SLA Warning", "Pricing Dispute", "Execution Delay", "Policy Override"]
STATUSES = ["OPEN", "IN_PROGRESS", "WAITING_FOR_INPUT", "PENDING_APPROVAL", "RESOLVED", "CLOSED"]


def generate_next_ticket_id(db_path: Optional[str] = None) -> str:
    """Generates sequential ticket ID: TKT-2026-0001."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id FROM tickets WHERE ticket_id LIKE 'TKT-2026-%' ORDER BY ticket_id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "TKT-2026-0001"
    
    last_id_str = row["ticket_id"]
    try:
        last_seq = int(last_id_str.split("-")[-1])
        next_seq = last_seq + 1
        return f"TKT-2026-{next_seq:04d}"
    except Exception:
        return f"TKT-2026-{datetime.now().strftime('%M%S')}"


def create_ticket(
    request_id: str,
    merchant_id: str,
    assigned_team: str,
    priority: str,
    category: str,
    initial_comment: str,
    creator: str = "System",
    creator_role: str = "Pricing Operations",
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new service workflow ticket."""
    ticket_id = generate_next_ticket_id(db_path)
    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    updated_at = created_at
    
    # SLA due based on priority
    hours_map = {"CRITICAL": 12, "HIGH": 24, "MEDIUM": 48, "LOW": 72}
    sla_hours = hours_map.get(priority, 48)
    sla_due = (now + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M:%S")

    comments_list = [
        {
            "author": creator,
            "role": creator_role,
            "timestamp": created_at,
            "message": initial_comment
        }
    ]
    comments_json = json.dumps(comments_list)

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tickets (
        ticket_id, request_id, merchant_id, assigned_team, priority, category,
        status, sla_due, created_at, updated_at, comments, resolution
    ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, '')
    """, (
        ticket_id, request_id, merchant_id, assigned_team, priority, category,
        sla_due, created_at, updated_at, comments_json
    ))
    conn.commit()
    conn.close()

    log_audit_event(
        request_id=request_id,
        merchant_id=merchant_id,
        actor=creator,
        actor_role=creator_role,
        action="TICKET_CREATED",
        old_value=None,
        new_value=f"Ticket {ticket_id} [{priority}] assigned to {assigned_team}",
        reason=category,
        db_path=db_path
    )

    return get_ticket_by_id(ticket_id, db_path)


def get_ticket_by_id(ticket_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves single ticket by ticket ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT t.*, m.merchant_name, r.payment_method, r.current_stage
    FROM tickets t
    LEFT JOIN merchants m ON t.merchant_id = m.merchant_id
    LEFT JOIN pricing_requests r ON t.request_id = r.request_id
    WHERE t.ticket_id = ?
    """, (ticket_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    res = dict(row)
    try:
        res["comments_list"] = json.loads(res["comments"])
    except Exception:
        res["comments_list"] = []

    # Calculate SLA countdown
    now = datetime.now()
    try:
        due_dt = datetime.strptime(res["sla_due"], "%Y-%m-%d %H:%M:%S")
        if res["status"] in ["RESOLVED", "CLOSED"]:
            res["sla_status"] = "RESOLVED"
            res["time_remaining"] = "Resolved"
        else:
            diff = due_dt - now
            if diff.total_seconds() < 0:
                res["sla_status"] = "BREACHED"
                res["time_remaining"] = f"Overdue by {abs(diff.total_seconds())/3600:.1f}h"
            elif diff.total_seconds() < 43200: # <12h
                res["sla_status"] = "AT_RISK"
                res["time_remaining"] = f"{diff.total_seconds()/3600:.1f}h left"
            else:
                res["sla_status"] = "OK"
                res["time_remaining"] = f"{diff.total_seconds()/3600:.1f}h left"
    except Exception:
        res["sla_status"] = "UNKNOWN"
        res["time_remaining"] = "N/A"

    return res


def get_all_tickets(
    status_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves list of tickets with optional filtering."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = """
    SELECT t.*, m.merchant_name, r.payment_method, r.current_stage
    FROM tickets t
    LEFT JOIN merchants m ON t.merchant_id = m.merchant_id
    LEFT JOIN pricing_requests r ON t.request_id = r.request_id
    WHERE 1=1
    """
    params = []

    if status_filter and status_filter != "ALL":
        query += " AND t.status = ?"
        params.append(status_filter)

    if team_filter and team_filter != "ALL":
        query += " AND t.assigned_team = ?"
        params.append(team_filter)

    if priority_filter and priority_filter != "ALL":
        query += " AND t.priority = ?"
        params.append(priority_filter)

    query += " ORDER BY t.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    now = datetime.now()
    for r in rows:
        t = dict(r)
        try:
            t["comments_list"] = json.loads(t["comments"])
        except Exception:
            t["comments_list"] = []

        try:
            due_dt = datetime.strptime(t["sla_due"], "%Y-%m-%d %H:%M:%S")
            if t["status"] in ["RESOLVED", "CLOSED"]:
                t["sla_status"] = "RESOLVED"
            else:
                diff = due_dt - now
                if diff.total_seconds() < 0:
                    t["sla_status"] = "BREACHED"
                elif diff.total_seconds() < 43200:
                    t["sla_status"] = "AT_RISK"
                else:
                    t["sla_status"] = "OK"
        except Exception:
            t["sla_status"] = "UNKNOWN"

        results.append(t)

    return results


def add_ticket_comment(
    ticket_id: str,
    author: str,
    role: str,
    message: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Adds a new comment to an existing ticket."""
    tkt = get_ticket_by_id(ticket_id, db_path)
    if not tkt:
        raise ValueError(f"Ticket {ticket_id} not found.")

    comments_list = tkt.get("comments_list", [])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    comments_list.append({
        "author": author,
        "role": role,
        "timestamp": now_str,
        "message": message
    })

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE tickets
    SET comments = ?, updated_at = ?
    WHERE ticket_id = ?
    """, (json.dumps(comments_list), now_str, ticket_id))
    conn.commit()
    conn.close()

    return get_ticket_by_id(ticket_id, db_path)


def update_ticket_status(
    ticket_id: str,
    new_status: str,
    assigned_team: Optional[str] = None,
    resolution: Optional[str] = None,
    updater: str = "User",
    updater_role: str = "Pricing Operations",
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Updates ticket status, team assignment, or resolution notes."""
    tkt = get_ticket_by_id(ticket_id, db_path)
    if not tkt:
        raise ValueError(f"Ticket {ticket_id} not found.")

    old_status = tkt["status"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    new_team = assigned_team or tkt["assigned_team"]
    res_text = resolution if resolution is not None else tkt["resolution"]

    cursor.execute("""
    UPDATE tickets
    SET status = ?, assigned_team = ?, resolution = ?, updated_at = ?
    WHERE ticket_id = ?
    """, (new_status, new_team, res_text, now_str, ticket_id))
    conn.commit()
    conn.close()

    log_audit_event(
        request_id=tkt["request_id"],
        merchant_id=tkt["merchant_id"],
        actor=updater,
        actor_role=updater_role,
        action="TICKET_UPDATED",
        old_value=f"Status: {old_status}",
        new_value=f"Status: {new_status}, Team: {new_team}",
        reason=resolution or "Ticket status updated",
        db_path=db_path
    )

    return get_ticket_by_id(ticket_id, db_path)
