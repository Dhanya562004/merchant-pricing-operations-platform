"""
Margin & Profitability Engine for Merchant Pricing Operations Platform.
Computes revenue, cost breakdowns, gross margins, and projected financial impacts.
"""
from typing import Dict, Any, Optional
import sqlite3
from src.database import get_connection


def calculate_financial_impact(
    monthly_gmv: float,
    transaction_count: int,
    current_mdr: float,
    proposed_mdr: float,
    current_fixed_fee: float,
    proposed_fixed_fee: float,
    network_cost_percent: float = 1.05,
    bank_cost_percent: float = 0.30,
    processing_cost_fixed: float = 0.05,
    other_op_cost_fixed: float = 0.02
) -> Dict[str, Any]:
    """
    Computes comprehensive transparent profitability metrics.
    
    Formulas:
        Current Revenue = (GMV * Current MDR %) + (Tx Count * Current Fixed Fee)
        Proposed Revenue = (GMV * Proposed MDR %) + (Tx Count * Proposed Fixed Fee)
        Total Processing Cost = (GMV * (Network Cost % + Bank Cost %)) + (Tx Count * (Processing Fixed + Other Op Fixed))
        Current Gross Margin = Current Revenue - Total Processing Cost
        Projected Gross Margin = Proposed Revenue - Total Processing Cost
        Current Margin % = (Current Gross Margin / Current Revenue) * 100
        Projected Margin % = (Projected Gross Margin / Proposed Revenue) * 100
        Monthly Revenue Impact = Proposed Revenue - Current Revenue
        Monthly Margin Impact = Projected Gross Margin - Current Gross Margin
        Annualized Revenue Impact = Monthly Revenue Impact * 12
        Annualized Margin Impact = Monthly Margin Impact * 12
    """
    # Defensive checks for non-zero transaction counts
    tx_count = max(1, transaction_count if transaction_count > 0 else 1000)

    # Revenues
    current_revenue = round((monthly_gmv * (current_mdr / 100.0)) + (tx_count * current_fixed_fee), 2)
    proposed_revenue = round((monthly_gmv * (proposed_mdr / 100.0)) + (tx_count * proposed_fixed_fee), 2)

    # Costs
    cost_percent = network_cost_percent + bank_cost_percent
    fixed_cost_per_tx = processing_cost_fixed + other_op_cost_fixed

    variable_cost = monthly_gmv * (cost_percent / 100.0)
    fixed_cost_total = tx_count * fixed_cost_per_tx
    total_processing_cost = round(variable_cost + fixed_cost_total, 2)

    # Margins
    current_gross_margin = round(current_revenue - total_processing_cost, 2)
    projected_gross_margin = round(proposed_revenue - total_processing_cost, 2)

    current_margin_pct = round((current_gross_margin / current_revenue * 100.0), 2) if current_revenue > 0 else 0.0
    projected_margin_pct = round((projected_gross_margin / proposed_revenue * 100.0), 2) if proposed_revenue > 0 else 0.0

    # Impacts
    monthly_revenue_impact = round(proposed_revenue - current_revenue, 2)
    monthly_margin_impact = round(projected_gross_margin - current_gross_margin, 2)

    annualized_revenue_impact = round(monthly_revenue_impact * 12.0, 2)
    annualized_margin_impact = round(monthly_margin_impact * 12.0, 2)

    return {
        "monthly_gmv": monthly_gmv,
        "transaction_count": tx_count,
        "current_revenue": current_revenue,
        "proposed_revenue": proposed_revenue,
        "total_processing_cost": total_processing_cost,
        "network_cost_percent": network_cost_percent,
        "bank_cost_percent": bank_cost_percent,
        "processing_cost_fixed": processing_cost_fixed,
        "other_op_cost_fixed": other_op_cost_fixed,
        "total_cost_percent": round(cost_percent, 4),
        "total_cost_fixed": round(fixed_cost_per_tx, 4),
        "current_gross_margin": current_gross_margin,
        "projected_gross_margin": projected_gross_margin,
        "current_margin_pct": current_margin_pct,
        "projected_margin_pct": projected_margin_pct,
        "monthly_revenue_impact": monthly_revenue_impact,
        "monthly_margin_impact": monthly_margin_impact,
        "annualized_revenue_impact": annualized_revenue_impact,
        "annualized_margin_impact": annualized_margin_impact,
        "is_loss_making": projected_gross_margin < 0
    }


def get_banking_costs_for_request(request_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches banking cost assumptions for a given pricing request."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM banking_costs WHERE request_id = ?", (request_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_banking_costs(
    request_id: str,
    network_cost_percent: float,
    bank_cost_percent: float,
    processing_cost_fixed: float,
    other_op_cost_fixed: float,
    notes: str,
    updated_by: str,
    db_path: Optional[str] = None
) -> None:
    """Inserts or updates banking cost assumptions for a request."""
    from datetime import datetime
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO banking_costs (request_id, network_cost_percent, bank_cost_percent, processing_cost_fixed, other_op_cost_fixed, notes, updated_by, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(request_id) DO UPDATE SET
        network_cost_percent = excluded.network_cost_percent,
        bank_cost_percent = excluded.bank_cost_percent,
        processing_cost_fixed = excluded.processing_cost_fixed,
        other_op_cost_fixed = excluded.other_op_cost_fixed,
        notes = excluded.notes,
        updated_by = excluded.updated_by,
        updated_at = excluded.updated_at
    """, (request_id, network_cost_percent, bank_cost_percent, processing_cost_fixed, other_op_cost_fixed, notes, updated_by, now_str))

    conn.commit()
    conn.close()
