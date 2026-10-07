"""
Unit tests for Ticket Engine, SLA tracking, and Audit Log logging.
"""
import pytest
import os
import tempfile
from src.database import init_db, reset_database
from src.ticket_engine import create_ticket, get_ticket_by_id, add_ticket_comment, update_ticket_status, get_all_tickets
from src.audit_engine import log_audit_event, get_audit_logs


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


def test_create_and_get_ticket(temp_db):
    tkt = create_ticket(
        request_id="PR-2026-0001",
        merchant_id="MERCH-1001",
        assigned_team="Banking Operations",
        priority="HIGH",
        category="Margin Review",
        initial_comment="Testing ticket creation",
        creator="Unit Tester",
        creator_role="Pricing Analyst",
        db_path=temp_db
    )

    assert tkt is not None
    assert tkt["ticket_id"].startswith("TKT-2026-")
    assert tkt["assigned_team"] == "Banking Operations"
    assert tkt["priority"] == "HIGH"
    assert len(tkt["comments_list"]) == 1


def test_ticket_comments_and_status_update(temp_db):
    tkt = create_ticket(
        request_id="PR-2026-0002",
        merchant_id="MERCH-1002",
        assigned_team="Checker Team",
        priority="MEDIUM",
        category="SLA Warning",
        initial_comment="Initial ticket body",
        db_path=temp_db
    )

    tkt_id = tkt["ticket_id"]
    updated_tkt = add_ticket_comment(tkt_id, "Smita Rao", "Banking Operations", "Follow up comment", db_path=temp_db)
    assert len(updated_tkt["comments_list"]) == 2

    res_tkt = update_ticket_status(
        ticket_id=tkt_id,
        new_status="RESOLVED",
        assigned_team="Finance",
        resolution="Resolved during unit testing",
        db_path=temp_db
    )
    assert res_tkt["status"] == "RESOLVED"
    assert res_tkt["assigned_team"] == "Finance"
    assert res_tkt["resolution"] == "Resolved during unit testing"


def test_audit_event_logging(temp_db):
    log_audit_event(
        request_id="PR-2026-9999",
        merchant_id="MERCH-1001",
        actor="Test Actor",
        actor_role="Pricing Analyst",
        action="TEST_ACTION",
        old_value="Old",
        new_value="New",
        reason="Unit testing audit event",
        db_path=temp_db
    )

    logs = get_audit_logs(action_filter="TEST_ACTION", db_path=temp_db)
    assert len(logs) >= 1
    assert logs[0]["request_id"] == "PR-2026-9999"
    assert logs[0]["action"] == "TEST_ACTION"
