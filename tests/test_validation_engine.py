"""
Unit tests for Deterministic Pricing Validation Engine.
"""
import pytest
import os
import tempfile
from src.database import init_db, reset_database
from src.validation_engine import validate_pricing_request


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


def test_validation_pass_clean(temp_db):
    res = validate_pricing_request(
        merchant_id="MERCH-1001",
        payment_method="Cards",
        current_mdr=1.85,
        proposed_mdr=1.75, # Small 5.4% drop
        current_fixed_fee=0.0,
        proposed_fixed_fee=0.0,
        effective_date_str="2026-05-01",
        reason="Standard annual volume tier adjustment",
        business_justification="Merchant achieved ₹15 Cr monthly GMV target tier.",
        expected_monthly_gmv=150000000.0,
        db_path=temp_db
    )

    assert res["overall_status"] in ["PASS", "WARNING"]
    assert res["is_eligible"] is True
    assert res["required_approval_level"] == "STANDARD"


def test_validation_checker_approval_required(temp_db):
    res = validate_pricing_request(
        merchant_id="MERCH-1001",
        payment_method="Cards",
        current_mdr=1.85,
        proposed_mdr=1.60, # 13.5% drop (>10% threshold)
        current_fixed_fee=0.0,
        proposed_fixed_fee=0.0,
        effective_date_str="2026-05-01",
        reason="Competitive match against PayU",
        business_justification="Merchant threatened churn due to lower rival offer.",
        expected_monthly_gmv=150000000.0,
        db_path=temp_db
    )

    assert res["overall_status"] == "WARNING"
    assert res["required_approval_level"] == "CHECKER"


def test_validation_function_head_approval_required(temp_db):
    res = validate_pricing_request(
        merchant_id="MERCH-1001",
        payment_method="Cards",
        current_mdr=1.85,
        proposed_mdr=1.40, # 24.3% drop (>20% threshold)
        current_fixed_fee=0.0,
        proposed_fixed_fee=0.0,
        effective_date_str="2026-05-01",
        reason="Key strategic anchor merchant renewal",
        business_justification="Anchor e-commerce partner renewal requiring executive approval.",
        expected_monthly_gmv=150000000.0,
        db_path=temp_db
    )

    assert res["overall_status"] == "WARNING"
    assert res["required_approval_level"] == "FUNCTION_HEAD"
    assert res["risk_level"] in ["HIGH RISK", "CRITICAL"]


def test_validation_blocked_negative_margin(temp_db):
    # Proposed MDR 0.50% below cost 1.35%
    res = validate_pricing_request(
        merchant_id="MERCH-1001",
        payment_method="Cards",
        current_mdr=1.85,
        proposed_mdr=0.50,
        current_fixed_fee=0.0,
        proposed_fixed_fee=0.0,
        effective_date_str="2026-05-01",
        reason="Aggressive pricing bid",
        business_justification="Attempting to offer zero margin deal.",
        expected_monthly_gmv=150000000.0,
        db_path=temp_db
    )

    assert res["overall_status"] == "BLOCKED"
    assert res["is_eligible"] is False
    assert any(r["rule"] == "Margin Profitability Check" and r["result"] == "BLOCKED" for r in res["rules_checked"])


def test_validation_blocked_suspended_merchant(temp_db):
    # MERCH-1013 is Suspended in seed data
    res = validate_pricing_request(
        merchant_id="MERCH-1013",
        payment_method="Cards",
        current_mdr=2.50,
        proposed_mdr=2.00,
        current_fixed_fee=5.0,
        proposed_fixed_fee=2.0,
        effective_date_str="2026-05-01",
        reason="Reinstatement pricing discount",
        business_justification="Attempting pricing change for suspended merchant.",
        expected_monthly_gmv=3200000.0,
        db_path=temp_db
    )

    assert res["overall_status"] == "BLOCKED"
    assert any(r["rule"] == "Merchant Status" and r["result"] == "BLOCKED" for r in res["rules_checked"])
