"""
Workflow Engine for Merchant Pricing Operations Platform.
Manages state transitions, stage progressions, SLA calculations, and pricing execution.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from src.database import get_connection
from src.audit_engine import log_audit_event


WORKFLOW_STAGES = [
    "DRAFT",
    "INITIAL_VALIDATION",
    "POC_REVIEW",
    "BANKING_MARGIN_VALIDATION",
    "CHECKER_REVIEW",
    "FUNCTION_HEAD_APPROVAL",
    "READY_FOR_EXECUTION",
    "EXECUTED",
    "REJECTED",
    "SENT_BACK"
]


def generate_next_request_id(db_path: Optional[str] = None) -> str:
    """Generates sequential request ID format: PR-2026-0001."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT request_id FROM pricing_requests WHERE request_id LIKE 'PR-2026-%' ORDER BY request_id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "PR-2026-0001"
    
    last_id_str = row["request_id"]
    try:
        last_seq = int(last_id_str.split("-")[-1])
        next_seq = last_seq + 1
        return f"PR-2026-{next_seq:04d}"
    except Exception:
        return f"PR-2026-{datetime.now().strftime('%M%S')}"


def create_pricing_request(
    merchant_id: str,
    payment_method: str,
    current_mdr: float,
    proposed_mdr: float,
    current_fixed_fee: float,
    proposed_fixed_fee: float,
    effective_date: str,
    reason: str,
    expected_monthly_gmv: float,
    requestor: str,
    business_justification: str,
    supporting_notes: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new pricing revamp request in DRAFT / INITIAL_VALIDATION stage.
    Runs validation engine to set initial risk level and required approval stage.
    """
    from src.validation_engine import validate_pricing_request
    
    request_id = generate_next_request_id(db_path)
    
    val_res = validate_pricing_request(
        merchant_id=merchant_id,
        payment_method=payment_method,
        current_mdr=current_mdr,
        proposed_mdr=proposed_mdr,
        current_fixed_fee=current_fixed_fee,
        proposed_fixed_fee=proposed_fixed_fee,
        effective_date_str=effective_date,
        reason=reason,
        business_justification=business_justification,
        expected_monthly_gmv=expected_monthly_gmv,
        request_id=request_id,
        db_path=db_path
    )

    risk_level = val_res["risk_level"]
    risk_reasons_json = json.dumps(val_res["risk_reasons"])
    req_approval = val_res["required_approval_level"]

    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    updated_at = created_at
    sla_deadline = (now + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")

    initial_stage = "INITIAL_VALIDATION" if val_res["is_eligible"] else "DRAFT"
    initial_status = "IN_PROGRESS" if val_res["is_eligible"] else "DRAFT"

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO pricing_requests (
        request_id, merchant_id, payment_method, current_mdr, proposed_mdr,
        current_fixed_fee, proposed_fixed_fee, effective_date, reason, expected_monthly_gmv,
        requestor, business_justification, supporting_notes, risk_level, risk_reasons,
        current_stage, required_approval_level, status, created_at, updated_at,
        sla_deadline, is_sla_breached
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        request_id, merchant_id, payment_method, current_mdr, proposed_mdr,
        current_fixed_fee, proposed_fixed_fee, effective_date, reason, expected_monthly_gmv,
        requestor, business_justification, supporting_notes, risk_level, risk_reasons_json,
        initial_stage, req_approval, initial_status, created_at, updated_at,
        sla_deadline
    ))

    conn.commit()
    conn.close()

    # Log Audit Event
    log_audit_event(
        request_id=request_id,
        merchant_id=merchant_id,
        actor=requestor,
        actor_role="Pricing Analyst",
        action="REQUEST_CREATED",
        old_value=None,
        new_value=f"Proposed MDR: {proposed_mdr}%, Fixed: ₹{proposed_fixed_fee}",
        reason=reason,
        db_path=db_path
    )

    if initial_stage == "INITIAL_VALIDATION":
        log_audit_event(
            request_id=request_id,
            merchant_id=merchant_id,
            actor=requestor,
            actor_role="Pricing Analyst",
            action="REQUEST_SUBMITTED",
            old_value="DRAFT",
            new_value="INITIAL_VALIDATION",
            reason="Submitted for workflow review",
            db_path=db_path
        )

    return get_request_by_id(request_id, db_path)


def get_request_by_id(request_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves full request details by request ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT r.*, m.merchant_name, m.merchant_tier, m.industry, m.account_manager, m.current_status as merchant_status
    FROM pricing_requests r
    JOIN merchants m ON r.merchant_id = m.merchant_id
    WHERE r.request_id = ?
    """, (request_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    res = dict(row)
    # Parse risk_reasons JSON
    try:
        res["risk_reasons_list"] = json.loads(res["risk_reasons"])
    except Exception:
        res["risk_reasons_list"] = []

    # Calculate SLA status dynamically
    now = datetime.now()
    try:
        deadline = datetime.strptime(res["sla_deadline"], "%Y-%m-%d %H:%M:%S")
        created = datetime.strptime(res["created_at"], "%Y-%m-%d %H:%M:%S")
        
        if res["status"] in ["EXECUTED", "REJECTED"]:
            res["sla_status"] = "COMPLETED"
            res["time_remaining_str"] = "Completed"
        else:
            time_left = deadline - now
            if time_left.total_seconds() < 0:
                res["sla_status"] = "BREACHED"
                res["is_sla_breached"] = 1
                hours_over = abs(time_left.total_seconds()) / 3600.0
                res["time_remaining_str"] = f"Breached by {hours_over:.1f} hrs"
            elif time_left.total_seconds() < 43200: # < 12 hours remaining
                res["sla_status"] = "AT_RISK"
                hours_left = time_left.total_seconds() / 3600.0
                res["time_remaining_str"] = f"{hours_left:.1f} hrs left"
            else:
                res["sla_status"] = "OK"
                hours_left = time_left.total_seconds() / 3600.0
                res["time_remaining_str"] = f"{hours_left:.1f} hrs left"
    except Exception:
        res["sla_status"] = "UNKNOWN"
        res["time_remaining_str"] = "N/A"

    return res


def get_all_requests(
    status_filter: Optional[str] = None,
    stage_filter: Optional[str] = None,
    payment_filter: Optional[str] = None,
    risk_filter: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves list of pricing requests with optional filters."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = """
    SELECT r.*, m.merchant_name, m.merchant_tier, m.industry
    FROM pricing_requests r
    JOIN merchants m ON r.merchant_id = m.merchant_id
    WHERE 1=1
    """
    params = []

    if status_filter and status_filter != "ALL":
        query += " AND r.status = ?"
        params.append(status_filter)

    if stage_filter and stage_filter != "ALL":
        query += " AND r.current_stage = ?"
        params.append(stage_filter)

    if payment_filter and payment_filter != "ALL":
        query += " AND r.payment_method = ?"
        params.append(payment_filter)

    if risk_filter and risk_filter != "ALL":
        query += " AND r.risk_level = ?"
        params.append(risk_filter)

    query += " ORDER BY r.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        req = dict(r)
        # Parse JSON
        try:
            req["risk_reasons_list"] = json.loads(req["risk_reasons"])
        except Exception:
            req["risk_reasons_list"] = []
        result.append(req)

    return result


def advance_workflow_stage(
    request_id: str,
    next_stage: str,
    new_status: str,
    actor: str,
    actor_role: str,
    action_name: str,
    reason: str,
    db_path: Optional[str] = None
) -> None:
    """Updates request state and logs an immutable audit event."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT current_stage, status, merchant_id FROM pricing_requests WHERE request_id = ?", (request_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Request {request_id} not found.")

    old_stage = row["current_stage"]
    merchant_id = row["merchant_id"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE pricing_requests
    SET current_stage = ?, status = ?, updated_at = ?
    WHERE request_id = ?
    """, (next_stage, new_status, now_str, request_id))

    conn.commit()
    conn.close()

    # Log audit
    log_audit_event(
        request_id=request_id,
        merchant_id=merchant_id,
        actor=actor,
        actor_role=actor_role,
        action=action_name,
        old_value=old_stage,
        new_value=next_stage,
        reason=reason,
        db_path=db_path
    )


def execute_pricing_change(
    request_id: str,
    executor: str,
    executor_role: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes an approved pricing request:
    1. Updates merchant_pricing_config active row to SUPERSEDED
    2. Inserts new ACTIVE row with proposed MDR & fixed fee
    3. Updates request status to EXECUTED
    4. Logs PRICING_EXECUTED audit event
    """
    req = get_request_by_id(request_id, db_path)
    if not req:
        raise ValueError(f"Request {request_id} not found.")

    if req["current_stage"] != "READY_FOR_EXECUTION" and req["status"] != "APPROVED":
        raise ValueError(f"Request {request_id} is in stage '{req['current_stage']}' and status '{req['status']}' and cannot be executed directly until all approvals are complete.")

    merchant_id = req["merchant_id"]
    payment_method = req["payment_method"]
    proposed_mdr = req["proposed_mdr"]
    proposed_fixed = req["proposed_fixed_fee"]
    effective_date = req["effective_date"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Mark existing ACTIVE pricing configs as SUPERSEDED
    cursor.execute("""
    UPDATE merchant_pricing_config
    SET pricing_status = 'SUPERSEDED', effective_to = ?
    WHERE merchant_id = ? AND payment_method = ? AND pricing_status = 'ACTIVE'
    """, (effective_date, merchant_id, payment_method))

    # Insert new ACTIVE pricing configuration
    cursor.execute("""
    INSERT INTO merchant_pricing_config (
        merchant_id, payment_method, mdr_percent, fixed_fee, minimum_fee, maximum_fee,
        effective_from, effective_to, pricing_status, last_updated_by, last_updated_at
    ) VALUES (?, ?, ?, ?, 0.0, 0.0, ?, NULL, 'ACTIVE', ?, ?)
    """, (merchant_id, payment_method, proposed_mdr, proposed_fixed, effective_date, executor, now_str))

    # Mark request as EXECUTED
    cursor.execute("""
    UPDATE pricing_requests
    SET current_stage = 'READY_FOR_EXECUTION', status = 'EXECUTED', updated_at = ?
    WHERE request_id = ?
    """, (now_str, request_id))

    conn.commit()
    conn.close()

    # Log audit record
    log_audit_event(
        request_id=request_id,
        merchant_id=merchant_id,
        actor=executor,
        actor_role=executor_role,
        action="PRICING_EXECUTED",
        old_value=f"Old MDR: {req['current_mdr']}%, Fixed: ₹{req['current_fixed_fee']}",
        new_value=f"New Active MDR: {proposed_mdr}%, Fixed: ₹{proposed_fixed}",
        reason="Operational execution of approved pricing revamp request",
        db_path=db_path
    )

    return get_request_by_id(request_id, db_path)
