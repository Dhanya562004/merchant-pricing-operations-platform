"""
Pricing Engine for Merchant Pricing Operations Platform.
Handles merchant queries, active pricing retrieval, pricing comparisons, and revenue projections.
"""
import sqlite3
from typing import Dict, Any, List, Optional
from src.database import get_connection
from src.models import Merchant, PricingConfig


def get_all_merchants(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all merchants as a list of dictionaries."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM merchants ORDER BY merchant_name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_merchant_by_id(merchant_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Returns a specific merchant by ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM merchants WHERE merchant_id = ?", (merchant_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_pricing(merchant_id: str, payment_method: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Returns current active pricing config for a merchant and payment method."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM merchant_pricing_config
    WHERE merchant_id = ? AND payment_method = ? AND pricing_status = 'ACTIVE'
    ORDER BY id DESC LIMIT 1
    """, (merchant_id, payment_method))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_merchant_all_pricing(merchant_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all active pricing configurations for a merchant across payment methods."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM merchant_pricing_config
    WHERE merchant_id = ? AND pricing_status = 'ACTIVE'
    ORDER BY payment_method ASC
    """, (merchant_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_active_pricing(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all active merchant pricing configs joined with merchant details."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*, m.merchant_name, m.merchant_tier, m.industry, m.monthly_gmv
    FROM merchant_pricing_config p
    JOIN merchants m ON p.merchant_id = m.merchant_id
    WHERE p.pricing_status = 'ACTIVE'
    ORDER BY m.merchant_name ASC, p.payment_method ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def compare_pricing(current_mdr: float, proposed_mdr: float,
                    current_fixed: float, proposed_fixed: float) -> Dict[str, Any]:
    """
    Computes comparative metrics between current and proposed pricing.
    
    Returns:
        mdr_delta: proposed_mdr - current_mdr
        mdr_reduction_percent: percentage drop relative to current_mdr
        fixed_fee_delta: proposed_fixed - current_fixed
        fixed_fee_reduction_percent: percentage drop relative to current_fixed
    """
    mdr_delta = round(proposed_mdr - current_mdr, 4)
    if current_mdr > 0:
        mdr_reduction_pct = round(((current_mdr - proposed_mdr) / current_mdr) * 100.0, 2)
    else:
        mdr_reduction_pct = 0.0 if proposed_mdr == 0 else -100.0

    fixed_delta = round(proposed_fixed - current_fixed, 2)
    if current_fixed > 0:
        fixed_reduction_pct = round(((current_fixed - proposed_fixed) / current_fixed) * 100.0, 2)
    else:
        fixed_reduction_pct = 0.0 if proposed_fixed == 0 else -100.0

    return {
        "current_mdr": current_mdr,
        "proposed_mdr": proposed_mdr,
        "mdr_delta": mdr_delta,
        "mdr_reduction_pct": mdr_reduction_pct,
        "current_fixed_fee": current_fixed,
        "proposed_fixed_fee": proposed_fixed,
        "fixed_fee_delta": fixed_delta,
        "fixed_fee_reduction_pct": fixed_reduction_pct
    }


def calculate_per_transaction_revenue(gmv: float, mdr_pct: float, fixed_fee: float) -> float:
    """Calculates gross revenue per transaction or batch."""
    return round((gmv * (mdr_pct / 100.0)) + fixed_fee, 2)
