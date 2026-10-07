"""
Unit tests for Approval Hierarchy Engine and role-gated decision processing.
"""
import pytest
import os
import tempfile
from src.database import init_db, reset_database
from src.approval_engine import can_role_approve_stage, process_approval_decision, get_approval_history
from src.workflow_engine import get_request_by_id


@pytest.fixture
def temp_db():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    init_db(db_path)
    reset_database(db_path)
    yield db_path
    os.close(db_fd)
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


def test_can_role_approve_stage():
    assert can_role_approve_stage("POC Reviewer", "POC_REVIEW") is True
    assert can_role_approve_stage("Banking Operations", "POC_REVIEW") is False
    assert can_role_approve_stage("Operations Admin", "POC_REVIEW") is True

    assert can_role_approve_stage("Checker", "CHECKER_REVIEW") is True
    assert can_role_approve_stage("Pricing Analyst", "CHECKER_REVIEW") is False

    assert can_role_approve_stage("Function Head", "FUNCTION_HEAD_APPROVAL") is True
    assert can_role_approve_stage("Checker", "FUNCTION_HEAD_APPROVAL") is False


def test_process_approval_decision_approve(temp_db):
    # PR-2026-0006 is in POC_REVIEW stage
    res = process_approval_decision(
        request_id="PR-2026-0006",
        reviewer="Amit Roy",
        reviewer_role="POC Reviewer",
        decision="APPROVE",
        comments="POC review verified cleanly.",
        reason="Met tier requirements",
        db_path=temp_db
    )

    assert res["current_stage"] == "BANKING_MARGIN_VALIDATION"
    assert res["status"] == "IN_PROGRESS"


def test_process_approval_decision_unauthorized_role(temp_db):
    # PR-2026-0006 is in POC_REVIEW stage; Banking Operations cannot approve POC_REVIEW
    with pytest.raises(PermissionError):
        process_approval_decision(
            request_id="PR-2026-0006",
            reviewer="Smita Rao",
            reviewer_role="Banking Operations",
            decision="APPROVE",
            comments="Unauthorized attempt",
            reason="Test",
            db_path=temp_db
        )


def test_process_approval_decision_reject(temp_db):
    res = process_approval_decision(
        request_id="PR-2026-0006",
        reviewer="Amit Roy",
        reviewer_role="POC Reviewer",
        decision="REJECT",
        comments="Volume commitments unverified.",
        reason="Incomplete Risk Clearance",
        db_path=temp_db
    )

    assert res["current_stage"] == "REJECTED"
    assert res["status"] == "REJECTED"


def test_process_approval_decision_send_back(temp_db):
    res = process_approval_decision(
        request_id="PR-2026-0006",
        reviewer="Amit Roy",
        reviewer_role="POC Reviewer",
        decision="SEND BACK",
        comments="Please provide updated competitor rate card.",
        reason="Unjustified Price Cut",
        db_path=temp_db
    )

    assert res["current_stage"] == "SENT_BACK"
    assert res["status"] == "SENT_BACK"
