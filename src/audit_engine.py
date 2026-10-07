"""
Audit Engine for Merchant Pricing Operations Platform.
Provides immutable audit trail logging and filtering capabilities for operational governance.
"""
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.database import get_connection


def log_audit_event(
    request_id: Optional[str],
    merchant_id: Optional[str],
    actor: str,
    actor_role: str,
    action: str,
    old_value: Optional[str],
    new_value: Optional[str],
    reason: Optional[str],
    db_path: Optional[str] = None
) -> None:
    """Inserts an immutable audit record into audit_logs table."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO audit_logs (
        request_id, merchant_id, actor, actor_role, action,
        old_value, new_value, reason, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request_id, merchant_id, actor, actor_role, action,
        old_value, new_value, reason, now_str
    ))
    conn.commit()
    conn.close()


def get_audit_logs(
    request_id: Optional[str] = None,
    merchant_id: Optional[str] = None,
    action_filter: Optional[str] = None,
    actor_filter: Optional[str] = None,
    limit: int = 200,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Queries audit logs with optional filters."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = """
    SELECT a.*, m.merchant_name
    FROM audit_logs a
    LEFT JOIN merchants m ON a.merchant_id = m.merchant_id
    WHERE 1=1
    """
    params = []

    if request_id:
        query += " AND a.request_id = ?"
        params.append(request_id)

    if merchant_id:
        query += " AND a.merchant_id = ?"
        params.append(merchant_id)

    if action_filter and action_filter != "ALL":
        query += " AND a.action = ?"
        params.append(action_filter)

    if actor_filter and actor_filter != "ALL":
        query += " AND a.actor = ?"
        params.append(actor_filter)

    query += " ORDER BY a.event_id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]
