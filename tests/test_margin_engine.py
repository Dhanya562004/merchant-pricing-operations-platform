"""
Unit tests for Margin & Profitability Engine calculations.
"""
import pytest
import os
import tempfile
from src.database import init_db, reset_database
from src.margin_engine import calculate_financial_impact, get_banking_costs_for_request, save_banking_costs


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


def test_calculate_financial_impact_basic():
    fin = calculate_financial_impact(
        monthly_gmv=1000000.0, # ₹10 Lakhs
        transaction_count=1000,
        current_mdr=2.0,       # Rev = 20,000
        proposed_mdr=1.8,      # Rev = 18,000
        current_fixed_fee=0.0,
        proposed_fixed_fee=0.0,
        network_cost_percent=1.0, # Cost = 10,000 + 3,000 = 13,000
        bank_cost_percent=0.3,
        processing_cost_fixed=0.0,
        other_op_cost_fixed=0.0
    )

    assert fin["current_revenue"] == 20000.0
    assert fin["proposed_revenue"] == 18000.0
    assert fin["total_processing_cost"] == 13000.0
    assert fin["current_gross_margin"] == 7000.0
    assert fin["projected_gross_margin"] == 5000.0
    assert fin["monthly_revenue_impact"] == -2000.0
    assert fin["annualized_revenue_impact"] == -24000.0
    assert fin["is_loss_making"] is False


def test_calculate_financial_impact_loss_making():
    # Proposed MDR 0.90% below total cost 1.35% (1.05% + 0.30%)
    fin = calculate_financial_impact(
        monthly_gmv=1000000.0,
        transaction_count=1000,
        current_mdr=2.0,
        proposed_mdr=0.9,
        current_fixed_fee=0.0,
        proposed_fixed_fee=0.0,
        network_cost_percent=1.05,
        bank_cost_percent=0.30,
        processing_cost_fixed=0.0,
        other_op_cost_fixed=0.0
    )

    assert fin["projected_gross_margin"] < 0
    assert fin["is_loss_making"] is True


def test_save_and_get_banking_costs(temp_db):
    req_id = "PR-2026-TEST01"
    save_banking_costs(
        request_id=req_id,
        network_cost_percent=1.10,
        bank_cost_percent=0.35,
        processing_cost_fixed=0.05,
        other_op_cost_fixed=0.02,
        notes="Test rate card notes",
        updated_by="Banking Ops Test",
        db_path=temp_db
    )

    b_costs = get_banking_costs_for_request(req_id, temp_db)
    assert b_costs is not None
    assert b_costs["network_cost_percent"] == 1.10
    assert b_costs["bank_cost_percent"] == 0.35
    assert b_costs["notes"] == "Test rate card notes"
