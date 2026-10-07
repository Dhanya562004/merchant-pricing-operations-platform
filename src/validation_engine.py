"""
Deterministic Validation Engine for Merchant Pricing Operations Platform.
Validates pricing revamp requests against policy, data integrity, duplicate checks, and merchant state.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import sqlite3
from src.database import get_connection
from src.pricing_engine import compare_pricing
from src.margin_engine import calculate_financial_impact, get_banking_costs_for_request


def get_policy_config(db_path: Optional[str] = None) -> Dict[str, float]:
    """Loads active policy configuration thresholds from database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT policy_key, value FROM policy_config")
    rows = cursor.fetchall()
    conn.close()
    
    defaults = {
        "mdr_reduction_checker_threshold": 10.0,
        "mdr_reduction_fh_threshold": 20.0,
        "margin_fh_threshold": 5.0,
        "margin_block_threshold": 0.0,
        "gmv_high_risk_threshold": 50000000.0,
        "sla_standard_hours": 48.0
    }
    for r in rows:
        defaults[r["policy_key"]] = float(r["value"])
    return defaults


def validate_pricing_request(
    merchant_id: str,
    payment_method: str,
    current_mdr: float,
    proposed_mdr: float,
    current_fixed_fee: float,
    proposed_fixed_fee: float,
    effective_date_str: str,
    reason: str,
    business_justification: str,
    expected_monthly_gmv: float,
    request_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a deterministic suite of validation rules.
    
    Returns structured result:
    {
        "overall_status": "PASS" | "WARNING" | "BLOCKED",
        "is_eligible": bool,
        "rules_checked": [
            {"rule": str, "result": "PASS"|"WARNING"|"BLOCKED", "severity": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL", "explanation": str}
        ],
        "summary": str,
        "required_approval_level": "STANDARD" | "CHECKER" | "FUNCTION_HEAD",
        "risk_level": "LOW RISK" | "MEDIUM RISK" | "HIGH RISK" | "CRITICAL",
        "risk_reasons": list of str
    }
    """
    policies = get_policy_config(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    rules_checked = []
    risk_reasons = []

    # Rule 1: Required Fields Check
    missing_fields = []
    if not merchant_id: missing_fields.append("Merchant")
    if not payment_method: missing_fields.append("Payment Method")
    if not reason or len(reason.strip()) < 5: missing_fields.append("Reason")
    if not business_justification or len(business_justification.strip()) < 10: missing_fields.append("Business Justification")
    if not effective_date_str: missing_fields.append("Effective Date")

    if missing_fields:
        rules_checked.append({
            "rule": "Required Fields",
            "result": "BLOCKED",
            "severity": "CRITICAL",
            "explanation": f"Missing or incomplete required fields: {', '.join(missing_fields)}"
        })
    else:
        rules_checked.append({
            "rule": "Required Fields",
            "result": "PASS",
            "severity": "LOW",
            "explanation": "All required fields are present and satisfy minimum character length requirements."
        })

    # Rule 2: Valid Payment Method Check
    valid_methods = ["Cards", "UPI Recurring", "E-Mandate", "Optimiser"]
    if payment_method not in valid_methods:
        rules_checked.append({
            "rule": "Payment Method Validity",
            "result": "BLOCKED",
            "severity": "CRITICAL",
            "explanation": f"Invalid payment method '{payment_method}'. Supported methods: {', '.join(valid_methods)}"
        })
    else:
        rules_checked.append({
            "rule": "Payment Method Validity",
            "result": "PASS",
            "severity": "LOW",
            "explanation": f"Valid payment method '{payment_method}'."
        })

    # Rule 3: Merchant Status Check
    cursor.execute("SELECT merchant_name, current_status, merchant_tier, monthly_gmv, transaction_count FROM merchants WHERE merchant_id = ?", (merchant_id,))
    merchant_row = cursor.fetchone()
    
    merchant_status = "Active"
    merchant_gmv = expected_monthly_gmv
    tx_count = 10000

    if not merchant_row:
        rules_checked.append({
            "rule": "Merchant Existence",
            "result": "BLOCKED",
            "severity": "CRITICAL",
            "explanation": f"Merchant ID '{merchant_id}' not found in merchant master database."
        })
    else:
        merchant_status = merchant_row["current_status"]
        if expected_monthly_gmv <= 0:
            merchant_gmv = float(merchant_row["monthly_gmv"])
        tx_count = int(merchant_row["transaction_count"])

        if merchant_status == "Suspended":
            rules_checked.append({
                "rule": "Merchant Status",
                "result": "BLOCKED",
                "severity": "CRITICAL",
                "explanation": f"Merchant '{merchant_row['merchant_name']}' is SUSPENDED. Pricing revamp blocked until reinstated."
            })
            risk_reasons.append("Merchant account is Suspended")
        elif merchant_status == "Under Review":
            rules_checked.append({
                "rule": "Merchant Status",
                "result": "WARNING",
                "severity": "HIGH",
                "explanation": f"Merchant '{merchant_row['merchant_name']}' is UNDER REVIEW by Risk/Compliance."
            })
            risk_reasons.append("Merchant status is Under Review")
        else:
            rules_checked.append({
                "rule": "Merchant Status",
                "result": "PASS",
                "severity": "LOW",
                "explanation": f"Merchant '{merchant_row['merchant_name']}' is ACTIVE."
            })

    # Rule 4: Range Validation for MDR and Fixed Fee
    if proposed_mdr < 0.0 or proposed_mdr > 5.0:
        rules_checked.append({
            "rule": "MDR Range Bounds",
            "result": "BLOCKED",
            "severity": "CRITICAL",
            "explanation": f"Proposed MDR {proposed_mdr}% is outside permissible policy boundaries (0.0% to 5.0%)."
        })
    else:
        rules_checked.append({
            "rule": "MDR Range Bounds",
            "result": "PASS",
            "severity": "LOW",
            "explanation": f"Proposed MDR {proposed_mdr}% is within valid range [0.0%, 5.0%]."
        })

    if proposed_fixed_fee < 0.0 or proposed_fixed_fee > 500.0:
        rules_checked.append({
            "rule": "Fixed Fee Range Bounds",
            "result": "BLOCKED",
            "severity": "CRITICAL",
            "explanation": f"Proposed Fixed Fee ₹{proposed_fixed_fee} is outside permissible bounds (₹0 to ₹500)."
        })
    else:
        rules_checked.append({
            "rule": "Fixed Fee Range Bounds",
            "result": "PASS",
            "severity": "LOW",
            "explanation": f"Proposed Fixed Fee ₹{proposed_fixed_fee} is within valid bounds."
        })

    # Rule 5: Duplicate Pending Request Check
    query = """
    SELECT request_id, current_stage, status FROM pricing_requests
    WHERE merchant_id = ? AND payment_method = ? AND status IN ('DRAFT', 'IN_PROGRESS')
    """
    params = [merchant_id, payment_method]
    if request_id:
        query += " AND request_id != ?"
        params.append(request_id)
        
    cursor.execute(query, params)
    dup_row = cursor.fetchone()
    if dup_row:
        rules_checked.append({
            "rule": "Duplicate Request Check",
            "result": "BLOCKED",
            "severity": "HIGH",
            "explanation": f"An active pricing request ({dup_row['request_id']}) is already in progress ({dup_row['current_stage']}) for this merchant and payment method."
        })
    else:
        rules_checked.append({
            "rule": "Duplicate Request Check",
            "result": "PASS",
            "severity": "LOW",
            "explanation": "No duplicate active request found for this merchant & payment method."
        })

    # Rule 6: Effective Date Check
    try:
        eff_dt = datetime.strptime(effective_date_str, "%Y-%m-%d").date()
        today = date.today()
        if eff_dt < (today - timedelta(days=30)): # allow slight historical logging up to 30 days
            rules_checked.append({
                "rule": "Effective Date Range",
                "result": "WARNING",
                "severity": "MEDIUM",
                "explanation": f"Effective date ({effective_date_str}) is more than 30 days in the past."
            })
        else:
            rules_checked.append({
                "rule": "Effective Date Range",
                "result": "PASS",
                "severity": "LOW",
                "explanation": f"Effective date ({effective_date_str}) is valid."
            })
    except ValueError:
        rules_checked.append({
            "rule": "Effective Date Range",
            "result": "BLOCKED",
            "severity": "CRITICAL",
            "explanation": f"Invalid date format '{effective_date_str}'. Expected format YYYY-MM-DD."
        })

    # Rule 7: Pricing Reduction & Policy Governance Checks
    comp = compare_pricing(current_mdr, proposed_mdr, current_fixed_fee, proposed_fixed_fee)
    mdr_reduction_pct = comp["mdr_reduction_pct"]

    required_approval_level = "STANDARD"

    if mdr_reduction_pct > policies["mdr_reduction_fh_threshold"]: # > 20%
        rules_checked.append({
            "rule": "MDR Reduction Governance",
            "result": "WARNING",
            "severity": "HIGH",
            "explanation": f"Proposed MDR reduction of {mdr_reduction_pct}% exceeds {policies['mdr_reduction_fh_threshold']}% policy limit. Requires Function Head Approval."
        })
        required_approval_level = "FUNCTION_HEAD"
        risk_reasons.append(f"MDR reduction {mdr_reduction_pct}% > {policies['mdr_reduction_fh_threshold']}% threshold")
    elif mdr_reduction_pct > policies["mdr_reduction_checker_threshold"]: # > 10%
        rules_checked.append({
            "rule": "MDR Reduction Governance",
            "result": "WARNING",
            "severity": "MEDIUM",
            "explanation": f"Proposed MDR reduction of {mdr_reduction_pct}% exceeds {policies['mdr_reduction_checker_threshold']}% policy limit. Requires Checker Approval."
        })
        if required_approval_level != "FUNCTION_HEAD":
            required_approval_level = "CHECKER"
        risk_reasons.append(f"MDR reduction {mdr_reduction_pct}% > {policies['mdr_reduction_checker_threshold']}% threshold")
    else:
        rules_checked.append({
            "rule": "MDR Reduction Governance",
            "result": "PASS",
            "severity": "LOW",
            "explanation": f"Proposed MDR reduction of {mdr_reduction_pct}% is within standard approval limits."
        })

    # Rule 8: Margin / Profitability Check
    # Fetch banking cost assumptions if existing request
    banking_costs = None
    if request_id:
        banking_costs = get_banking_costs_for_request(request_id, db_path)

    net_cost = banking_costs["network_cost_percent"] if banking_costs else 1.05
    bank_cost = banking_costs["bank_cost_percent"] if banking_costs else 0.30
    proc_fixed = banking_costs["processing_cost_fixed"] if banking_costs else 0.05
    other_fixed = banking_costs["other_op_cost_fixed"] if banking_costs else 0.02

    fin_impact = calculate_financial_impact(
        monthly_gmv=merchant_gmv,
        transaction_count=tx_count,
        current_mdr=current_mdr,
        proposed_mdr=proposed_mdr,
        current_fixed_fee=current_fixed_fee,
        proposed_fixed_fee=proposed_fixed_fee,
        network_cost_percent=net_cost,
        bank_cost_percent=bank_cost,
        processing_cost_fixed=proc_fixed,
        other_op_cost_fixed=other_fixed
    )

    proj_margin_pct = fin_impact["projected_margin_pct"]
    proj_margin_val = fin_impact["projected_gross_margin"]

    if proj_margin_val < policies["margin_block_threshold"] or proj_margin_pct < 0: # Loss making
        rules_checked.append({
            "rule": "Margin Profitability Check",
            "result": "BLOCKED",
            "severity": "CRITICAL",
            "explanation": f"Projected Gross Margin ({proj_margin_pct}%, ₹{proj_margin_val:,.2f}) is NEGATIVE. Policy strictly blocks loss-making pricing."
        })
        risk_reasons.append("Projected Gross Margin is Negative (Loss Making)")
    elif proj_margin_pct < policies["margin_fh_threshold"]: # < 5%
        rules_checked.append({
            "rule": "Margin Profitability Check",
            "result": "WARNING",
            "severity": "HIGH",
            "explanation": f"Projected Gross Margin ({proj_margin_pct}%) is below {policies['margin_fh_threshold']}% policy limit. Requires Function Head Approval."
        })
        required_approval_level = "FUNCTION_HEAD"
        risk_reasons.append(f"Projected Gross Margin {proj_margin_pct}% < {policies['margin_fh_threshold']}% threshold")
    else:
        rules_checked.append({
            "rule": "Margin Profitability Check",
            "result": "PASS",
            "severity": "LOW",
            "explanation": f"Projected Gross Margin ({proj_margin_pct}%) satisfies policy profitability criteria."
        })

    # Rule 9: High GMV Scrutiny Check
    if merchant_gmv >= policies["gmv_high_risk_threshold"]: # > ₹5 Cr
        rules_checked.append({
            "rule": "Enterprise GMV Scrutiny",
            "result": "WARNING",
            "severity": "MEDIUM",
            "explanation": f"Merchant monthly GMV (₹{merchant_gmv:,.0f}) exceeds ₹5 Cr threshold. Under high operational scrutiny."
        })
        risk_reasons.append(f"Enterprise GMV >= ₹5 Cr")
    else:
        rules_checked.append({
            "rule": "Enterprise GMV Scrutiny",
            "result": "PASS",
            "severity": "LOW",
            "explanation": "Merchant monthly GMV is within standard operational volume tier."
        })

    conn.close()

    # Determine Overall Status & Risk Classification
    has_blocked = any(r["result"] == "BLOCKED" for r in rules_checked)
    has_warning = any(r["result"] == "WARNING" for r in rules_checked)

    if has_blocked:
        overall_status = "BLOCKED"
        is_eligible = False
        summary = "Pricing request is BLOCKED due to policy violations or negative margin."
    elif has_warning:
        overall_status = "WARNING"
        is_eligible = True
        summary = f"Pricing request passed with WARNINGS. Requires {required_approval_level} approval."
    else:
        overall_status = "PASS"
        is_eligible = True
        summary = "Pricing request passed all validation checks cleanly."

    # Risk Classification Logic
    if has_blocked or proj_margin_pct < 0 or merchant_status == "Suspended":
        risk_level = "CRITICAL"
    elif required_approval_level == "FUNCTION_HEAD" or len(risk_reasons) >= 2 or merchant_gmv >= 100000000:
        risk_level = "HIGH RISK"
    elif required_approval_level == "CHECKER" or len(risk_reasons) == 1:
        risk_level = "MEDIUM RISK"
    else:
        risk_level = "LOW RISK"

    return {
        "overall_status": overall_status,
        "is_eligible": is_eligible,
        "rules_checked": rules_checked,
        "summary": summary,
        "required_approval_level": required_approval_level,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "financial_impact": fin_impact,
        "comparison": comp
    }
