"""
Unit tests for Workflow Engine state machine and pricing execution.
"""
import pytest
import os
import tempfile
from src.database import init_db, reset_database, get_connection
from src.workflow_engine import (
    create_pricing_request,
    get_request_by_id,
    advance_workflow_stage,
    execute_pricing_change,
    generate_next_request_id
)
from src.pricing_engine import get_active_pricing


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


def test_generate_request_id(temp_db):
    req_id = generate_next_request_id(temp_db)
    assert req_id.startswith("PR-2026-")


def test_create_pricing_request(temp_db):
    req = create_pricing_request(
        merchant_id="MERCH-1001",
        payment_method="Cards",
        current_mdr=1.85,
        proposed_mdr=1.70,
        current_fixed_fee=0.0,
        proposed_fixed_fee=0.0,
        effective_date="2026-06-01",
        reason="Test unit creation request",
        expected_monthly_gmv=150000000.0,
        requestor="Unit Tester",
        business_justification="Comprehensive unit test justification for PR creation.",
        supporting_notes="Unit test notes",
        db_path=temp_db
    )

    assert req is not None
    assert req["merchant_id"] == "MERCH-1001"
    assert req["proposed_mdr"] == 1.70
    assert req["status"] in ["IN_PROGRESS", "DRAFT"]


def test_execute_pricing_change(temp_db):
    # PR-2026-0001 is READY_FOR_EXECUTION in seed data for MERCH-1001 Cards (Proposed MDR 1.70%)
    exec_req = execute_pricing_change(
        request_id="PR-2026-0001",
        executor="Tester",
        executor_role="Operations Admin",
        db_path=temp_db
    )

    assert exec_req["status"] == "EXECUTED"

    # Verify active merchant pricing config updated
    active_p = get_active_pricing("MERCH-1001", "Cards", temp_db)
    assert active_p is not None
    assert active_p["mdr_percent"] == 1.70
    assert active_p["pricing_status"] == "ACTIVE"


def test_unapproved_execution_rejected(temp_db):
    # PR-2026-0006 is in POC_REVIEW stage (unapproved)
    with pytest.raises(ValueError):
        execute_pricing_change(
            request_id="PR-2026-0006",
            executor="Tester",
            executor_role="Checker",
            db_path=temp_db
        )
