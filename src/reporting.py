"""
Reporting Engine for Merchant Pricing Operations Platform.
Generates structured DataFrames and CSV binary exports for operational reporting.
"""
import pandas as pd
from typing import Optional, Dict, Any
from src.database import get_connection
from src.workflow_engine import get_all_requests
from src.pricing_engine import get_all_active_pricing
from src.ticket_engine import get_all_tickets
from src.audit_engine import get_audit_logs


def generate_pricing_requests_report(db_path: Optional[str] = None) -> pd.DataFrame:
    """Generates comprehensive pricing request report DataFrame."""
    requests = get_all_requests(db_path=db_path)
    if not requests:
        return pd.DataFrame()
    
    df = pd.DataFrame(requests)
    cols_to_export = [
        "request_id", "merchant_id", "merchant_name", "merchant_tier", "industry",
        "payment_method", "current_mdr", "proposed_mdr", "current_fixed_fee",
        "proposed_fixed_fee", "effective_date", "reason", "expected_monthly_gmv",
        "requestor", "risk_level", "current_stage", "required_approval_level",
        "status", "created_at", "sla_deadline", "time_remaining_str"
    ]
    cols_present = [c for c in cols_to_export if c in df.columns]
    return df[cols_present]


def generate_merchant_pricing_report(db_path: Optional[str] = None) -> pd.DataFrame:
    """Generates active merchant pricing configuration report."""
    pricing = get_all_active_pricing(db_path=db_path)
    if not pricing:
        return pd.DataFrame()
    
    df = pd.DataFrame(pricing)
    cols = [
        "merchant_id", "merchant_name", "merchant_tier", "industry", "monthly_gmv",
        "payment_method", "mdr_percent", "fixed_fee", "minimum_fee", "maximum_fee",
        "effective_from", "pricing_status", "last_updated_by", "last_updated_at"
    ]
    cols_present = [c for c in cols if c in df.columns]
    return df[cols_present]


def generate_margin_impact_report(db_path: Optional[str] = None) -> pd.DataFrame:
    """Generates revenue and margin impact report for all active and approved requests."""
    from src.margin_engine import calculate_financial_impact, get_banking_costs_for_request
    requests = get_all_requests(db_path=db_path)
    
    rows = []
    for r in requests:
        req_id = r["request_id"]
        b_costs = get_banking_costs_for_request(req_id, db_path)
        net_cost = b_costs["network_cost_percent"] if b_costs else 1.05
        bank_cost = b_costs["bank_cost_percent"] if b_costs else 0.30
        proc_fixed = b_costs["processing_cost_fixed"] if b_costs else 0.05
        other_fixed = b_costs["other_op_cost_fixed"] if b_costs else 0.02

        fin = calculate_financial_impact(
            monthly_gmv=float(r["expected_monthly_gmv"]),
            transaction_count=10000,
            current_mdr=float(r["current_mdr"]),
            proposed_mdr=float(r["proposed_mdr"]),
            current_fixed_fee=float(r["current_fixed_fee"]),
            proposed_fixed_fee=float(r["proposed_fixed_fee"]),
            network_cost_percent=net_cost,
            bank_cost_percent=bank_cost,
            processing_cost_fixed=proc_fixed,
            other_op_cost_fixed=other_fixed
        )

        rows.append({
            "request_id": req_id,
            "merchant_id": r["merchant_id"],
            "merchant_name": r["merchant_name"],
            "payment_method": r["payment_method"],
            "monthly_gmv": r["expected_monthly_gmv"],
            "current_revenue": fin["current_revenue"],
            "proposed_revenue": fin["proposed_revenue"],
            "total_processing_cost": fin["total_processing_cost"],
            "current_gross_margin": fin["current_gross_margin"],
            "projected_gross_margin": fin["projected_gross_margin"],
            "projected_margin_pct": fin["projected_margin_pct"],
            "monthly_revenue_impact": fin["monthly_revenue_impact"],
            "monthly_margin_impact": fin["monthly_margin_impact"],
            "annualized_revenue_impact": fin["annualized_revenue_impact"],
            "annualized_margin_impact": fin["annualized_margin_impact"],
            "status": r["status"]
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def generate_approval_history_report(db_path: Optional[str] = None) -> pd.DataFrame:
    """Generates approval records history report."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, r.merchant_id, m.merchant_name, r.payment_method
    FROM approval_history a
    JOIN pricing_requests r ON a.request_id = r.request_id
    JOIN merchants m ON r.merchant_id = m.merchant_id
    ORDER BY a.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def generate_sla_performance_report(db_path: Optional[str] = None) -> pd.DataFrame:
    """Generates SLA monitoring and ticket turnaround report."""
    tickets = get_all_tickets(db_path=db_path)
    if not tickets:
        return pd.DataFrame()

    df = pd.DataFrame(tickets)
    cols = ["ticket_id", "request_id", "merchant_id", "merchant_name", "assigned_team", 
            "priority", "category", "status", "sla_status", "sla_due", "created_at", "updated_at"]
    cols_present = [c for c in cols if c in df.columns]
    return df[cols_present]


def generate_audit_log_report(db_path: Optional[str] = None) -> pd.DataFrame:
    """Generates audit log report."""
    logs = get_audit_logs(limit=1000, db_path=db_path)
    return pd.DataFrame(logs) if logs else pd.DataFrame()


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Converts a pandas DataFrame to UTF-8 encoded CSV bytes for download."""
    if df.empty:
        return b""
    return df.to_csv(index=False).encode("utf-8")
