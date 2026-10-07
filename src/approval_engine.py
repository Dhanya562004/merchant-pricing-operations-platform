"""
Approval Engine for Merchant Pricing Operations Platform.
Handles multi-level approval hierarchy, role authorization, and decision logging.
"""
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.database import get_connection
from src.audit_engine import log_audit_event
from src.workflow_engine import get_request_by_id, advance_workflow_stage


# Authorized roles per stage
STAGE_ROLE_MAP = {
    "POC_REVIEW": ["POC Reviewer", "Operations Admin"],
    "BANKING_MARGIN_VALIDATION": ["Banking Operations", "Operations Admin"],
    "CHECKER_REVIEW": ["Checker", "Operations Admin"],
    "FUNCTION_HEAD_APPROVAL": ["Function Head", "Operations Admin"]
}

# Progression path
STAGE_NEXT_MAP = {
    "INITIAL_VALIDATION": "POC_REVIEW",
    "POC_REVIEW": "BANKING_MARGIN_VALIDATION",
    "BANKING_MARGIN_VALIDATION": "CHECKER_REVIEW",
}


def can_role_approve_stage(role: str, stage: str) -> bool:
    """Checks if a user role is authorized to review/approve a specific stage."""
    allowed = STAGE_ROLE_MAP.get(stage, [])
    return role in allowed or role == "Operations Admin"


def get_approval_history(request_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves approval log history for a request."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM approval_history
    WHERE request_id = ?
    ORDER BY created_at ASC
    """, (request_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def process_approval_decision(
    request_id: str,
    reviewer: str,
    reviewer_role: str,
    decision: str,  # "APPROVE", "REJECT", "SEND BACK"
    comments: str,
    reason: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes an approval decision for a pricing request.
    
    Validates role permissions, updates request stage/status, records decision log.
    """
    req = get_request_by_id(request_id, db_path)
    if not req:
        raise ValueError(f"Request {request_id} not found.")

    current_stage = req["current_stage"]
    req_approval = req["required_approval_level"]

    # Validate role permissions
    if not can_role_approve_stage(reviewer_role, current_stage):
        allowed_roles = ", ".join(STAGE_ROLE_MAP.get(current_stage, ["Operations Admin"]))
        raise PermissionError(f"Role '{reviewer_role}' is not authorized to act on stage '{current_stage}'. Required role(s): {allowed_roles}")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Record decision in approval_history
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO approval_history (request_id, stage, reviewer, role, decision, comments, reason, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (request_id, current_stage, reviewer, reviewer_role, decision, comments, reason, now_str))
    conn.commit()
    conn.close()

    # Determine Next Stage
    if decision == "REJECT":
        advance_workflow_stage(
            request_id=request_id,
            next_stage="REJECTED",
            new_status="REJECTED",
            actor=reviewer,
            actor_role=reviewer_role,
            action_name="REQUEST_REJECTED",
            reason=f"Rejected at {current_stage}: {comments}",
            db_path=db_path
        )
    elif decision == "SEND BACK":
        advance_workflow_stage(
            request_id=request_id,
            next_stage="SENT_BACK",
            new_status="SENT_BACK",
            actor=reviewer,
            actor_role=reviewer_role,
            action_name="REQUEST_SENT_BACK",
            reason=f"Sent back at {current_stage}: {comments}",
            db_path=db_path
        )
    elif decision == "APPROVE":
        if current_stage == "POC_REVIEW":
            next_stage = "BANKING_MARGIN_VALIDATION"
            new_status = "IN_PROGRESS"
            action_name = "POC_APPROVED"

        elif current_stage == "BANKING_MARGIN_VALIDATION":
            next_stage = "CHECKER_REVIEW"
            new_status = "IN_PROGRESS"
            action_name = "BANKING_APPROVED"

        elif current_stage == "CHECKER_REVIEW":
            if req_approval == "FUNCTION_HEAD":
                next_stage = "FUNCTION_HEAD_APPROVAL"
                new_status = "IN_PROGRESS"
                action_name = "CHECKER_APPROVED"
            else:
                next_stage = "READY_FOR_EXECUTION"
                new_status = "APPROVED"
                action_name = "CHECKER_APPROVED"

        elif current_stage == "FUNCTION_HEAD_APPROVAL":
            next_stage = "READY_FOR_EXECUTION"
            new_status = "APPROVED"
            action_name = "FUNCTION_HEAD_APPROVED"

        elif current_stage == "INITIAL_VALIDATION":
            next_stage = "POC_REVIEW"
            new_status = "IN_PROGRESS"
            action_name = "VALIDATION_PASSED"

        else:
            next_stage = "READY_FOR_EXECUTION"
            new_status = "APPROVED"
            action_name = "STAGE_APPROVED"

        advance_workflow_stage(
            request_id=request_id,
            next_stage=next_stage,
            new_status=new_status,
            actor=reviewer,
            actor_role=reviewer_role,
            action_name=action_name,
            reason=f"Approved at {current_stage}: {comments}",
            db_path=db_path
        )

    return get_request_by_id(request_id, db_path)
