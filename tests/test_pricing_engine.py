"""
Unit tests for Pricing Engine and delta comparison metrics.
"""
import pytest
import os
import tempfile
from src.database import init_db, reset_database, get_connection
from src.pricing_engine import compare_pricing, calculate_per_transaction_revenue, get_all_merchants, get_active_pricing


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


def test_compare_pricing_mdr_reduction():
    # 2.0% -> 1.5% MDR reduction = 25% drop
    res = compare_pricing(current_mdr=2.0, proposed_mdr=1.5, current_fixed=0.0, proposed_fixed=0.0)
    assert res["mdr_delta"] == -0.5
    assert res["mdr_reduction_pct"] == 25.0


def test_compare_pricing_fixed_fee_reduction():
    # ₹10.0 -> ₹8.0 = 20% drop
    res = compare_pricing(current_mdr=1.8, proposed_mdr=1.8, current_fixed=10.0, proposed_fixed=8.0)
    assert res["fixed_fee_delta"] == -2.0
    assert res["fixed_fee_reduction_pct"] == 20.0


def test_per_transaction_revenue():
    # GMV ₹10,000 * 2.0% MDR + ₹5.0 fixed fee = ₹205.00
    rev = calculate_per_transaction_revenue(gmv=10000.0, mdr_pct=2.0, fixed_fee=5.0)
    assert rev == 205.00


def test_get_all_merchants_from_db(temp_db):
    merchants = get_all_merchants(temp_db)
    assert len(merchants) >= 12
    m1 = merchants[0]
    assert "merchant_id" in m1
    assert "merchant_name" in m1


def test_get_active_pricing_from_db(temp_db):
    pricing = get_active_pricing("MERCH-1001", "Cards", temp_db)
    assert pricing is not None
    assert pricing["payment_method"] == "Cards"
    assert pricing["pricing_status"] == "ACTIVE"
