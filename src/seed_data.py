"""
Seed dataset generator for Merchant Pricing Operations Platform.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional
from src.database import get_connection


def seed_all_data(db_path: Optional[str] = None) -> None:
    """Populates SQLite database with rich realistic demo data."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Clear existing data safely
    tables = ["audit_logs", "tickets", "approval_history", "banking_costs", 
              "pricing_requests", "merchant_pricing_config", "merchants", "policy_config"]
    for t in tables:
        cursor.execute(f"DELETE FROM {t}")

    # 1. Seed Policies
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    policies = [
        ("mdr_reduction_checker_threshold", "MDR Reduction % for Checker Approval", 10.0, "MDR reductions exceeding 10% require Checker review", now_str),
        ("mdr_reduction_fh_threshold", "MDR Reduction % for Function Head Approval", 20.0, "MDR reductions exceeding 20% require Function Head review", now_str),
        ("margin_fh_threshold", "Gross Margin % Threshold for Function Head Approval", 5.0, "Projected Gross Margin < 5% requires Function Head approval", now_str),
        ("margin_block_threshold", "Gross Margin % Minimum (Hard Stop)", 0.0, "Projected Gross Margin < 0% (loss making) is automatically blocked", now_str),
        ("gmv_high_risk_threshold", "GMV High Scrutiny Threshold (INR)", 50000000.0, "Merchants with Monthly GMV > ₹5 Cr trigger high risk review", now_str),
        ("sla_standard_hours", "Standard Operations SLA (Hours)", 48.0, "Standard turnaround SLA target for pricing revamp requests", now_str),
    ]
    cursor.executemany("""
    INSERT INTO policy_config (policy_key, policy_name, value, description, updated_at)
    VALUES (?, ?, ?, ?, ?)
    """, policies)

    # 2. Seed Merchants (14 merchants)
    merchants = [
        ("MERCH-1001", "Aura Retail Pvt Ltd", "E-Commerce", "Enterprise", 150000000.0, 450000, "Active", "Rajesh Sharma", "Low"),
        ("MERCH-1002", "Nexus Gaming Technologies", "Gaming", "Enterprise", 85000000.0, 920000, "Active", "Ananya Verma", "Medium"),
        ("MERCH-1003", "EduSpark Digital Learn", "EdTech", "Mid-Market", 22000000.0, 85000, "Active", "Vikram Patel", "Low"),
        ("MERCH-1004", "CloudPay SaaS Solutions", "SaaS", "Enterprise", 120000000.0, 65000, "Active", "Rajesh Sharma", "Low"),
        ("MERCH-1005", "SwiftCart Logistics", "Quick Commerce", "Enterprise", 210000000.0, 1800000, "Active", "Priya Nair", "High"),
        ("MERCH-1006", "VoyageAir Travels", "Travel", "Enterprise", 95000000.0, 120000, "Active", "Ananya Verma", "Medium"),
        ("MERCH-1007", "HealthFirst Diagnostics", "Healthcare", "Mid-Market", 18000000.0, 42000, "Active", "Vikram Patel", "Low"),
        ("MERCH-1008", "UrbanBites Foods", "Food & Beverage", "Mid-Market", 34000000.0, 310000, "Active", "Priya Nair", "Low"),
        ("MERCH-1009", "ZingPay Retailers", "Retail", "SMB", 4500000.0, 15000, "Active", "Karan Mehta", "Low"),
        ("MERCH-1010", "NovaStream Entertainment", "OTT / Media", "Mid-Market", 48000000.0, 620000, "Under Review", "Karan Mehta", "High"),
        ("MERCH-1011", "PrimeDistro Wholesale", "B2B Commerce", "Enterprise", 175000000.0, 75000, "Active", "Rajesh Sharma", "Medium"),
        ("MERCH-1012", "FinEdge Insurance", "BFSI", "Enterprise", 140000000.0, 210000, "Active", "Priya Nair", "Low"),
        ("MERCH-1013", "OmniFit Fitness Network", "Wellness", "SMB", 3200000.0, 11000, "Suspended", "Karan Mehta", "High"),
        ("MERCH-1014", "Skyline Infra Pay", "Real Estate", "Mid-Market", 28000000.0, 4800, "Active", "Vikram Patel", "Medium"),
    ]
    cursor.executemany("""
    INSERT INTO merchants (merchant_id, merchant_name, industry, merchant_tier, monthly_gmv, transaction_count, current_status, account_manager, risk_category)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, merchants)

    # 3. Seed Merchant Pricing Configurations
    configs = [
        # Cards
        ("MERCH-1001", "Cards", 1.85, 0.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1002", "Cards", 1.95, 0.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1003", "Cards", 2.10, 2.0, 0.0, 0.0, "2025-02-15", None, "ACTIVE", "ops_admin", "2025-02-15 11:30:00"),
        ("MERCH-1004", "Cards", 1.75, 0.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1005", "Cards", 1.65, 0.0, 0.0, 0.0, "2025-03-01", None, "ACTIVE", "ops_admin", "2025-03-01 09:00:00"),
        ("MERCH-1006", "Cards", 1.90, 0.0, 0.0, 0.0, "2025-01-10", None, "ACTIVE", "ops_admin", "2025-01-10 14:00:00"),
        ("MERCH-1007", "Cards", 2.20, 3.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1008", "Cards", 1.95, 1.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1009", "Cards", 2.40, 5.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1010", "Cards", 2.00, 0.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1011", "Cards", 1.70, 0.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1012", "Cards", 1.80, 0.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1013", "Cards", 2.50, 5.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1014", "Cards", 2.00, 2.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),

        # UPI Recurring
        ("MERCH-1001", "UPI Recurring", 0.15, 4.0, 0.0, 15.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1003", "UPI Recurring", 0.20, 5.0, 0.0, 20.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1004", "UPI Recurring", 0.12, 3.5, 0.0, 12.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1010", "UPI Recurring", 0.18, 4.5, 0.0, 18.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),

        # E-Mandate
        ("MERCH-1004", "E-Mandate", 0.0, 12.0, 10.0, 50.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1012", "E-Mandate", 0.0, 10.0, 8.0, 45.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),

        # Optimiser
        ("MERCH-1001", "Optimiser", 0.05, 1.5, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
        ("MERCH-1005", "Optimiser", 0.04, 1.0, 0.0, 0.0, "2025-01-01", None, "ACTIVE", "ops_admin", "2025-01-01 10:00:00"),
    ]
    cursor.executemany("""
    INSERT INTO merchant_pricing_config (merchant_id, payment_method, mdr_percent, fixed_fee, minimum_fee, maximum_fee, effective_from, effective_to, pricing_status, last_updated_by, last_updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, configs)

    # 4. Seed Pricing Revamp Requests (22 requests at various stages)
    base_time = datetime.now()
    
    requests_data = [
        # 1. EXECUTED (Standard approval)
        ("PR-2026-0001", "MERCH-1001", "Cards", 1.85, 1.70, 0.0, 0.0, "2026-03-01", "Volume tier upgrade request", 150000000.0,
         "Rahul Verma", "Merchant reached ₹15 Cr monthly GMV tier threshold", "Competitor offering 1.68%", "LOW RISK",
         json.dumps(["Volume tier discount standard"]), "READY_FOR_EXECUTION", "STANDARD", "EXECUTED",
         (base_time - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 2. READY_FOR_EXECUTION (Checker approval passed)
        ("PR-2026-0002", "MERCH-1002", "Cards", 1.95, 1.65, 0.0, 0.0, "2026-03-15", "Competitive match against PayU", 85000000.0,
         "Neha Sen", "Merchant threatened churn of ₹8.5 Cr GMV due to rival bid", "Attach bank NOC letter", "HIGH RISK",
         json.dumps(["MDR reduction > 15%", "Enterprise merchant high churn risk"]), "READY_FOR_EXECUTION", "CHECKER", "APPROVED",
         (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 3. FUNCTION_HEAD_APPROVAL (High Risk - >20% MDR drop)
        ("PR-2026-0003", "MERCH-1005", "Cards", 1.65, 1.25, 0.0, 0.0, "2026-04-01", "Strategic key account renewal", 210000000.0,
         "Rahul Verma", "Anchor merchant in quick commerce seeking ultra-low rates", "Margin compressed to 3.8%", "HIGH RISK",
         json.dumps(["MDR reduction 24.2% (>20% threshold)", "Projected Margin 3.8% (<5% threshold)", "GMV > ₹50M"]), "FUNCTION_HEAD_APPROVAL", "FUNCTION_HEAD", "IN_PROGRESS",
         (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 4. CHECKER_REVIEW
        ("PR-2026-0004", "MERCH-1003", "Cards", 2.10, 1.85, 2.0, 1.5, "2026-03-20", "Annual contract renegotiation", 22000000.0,
         "Siddharth Rao", "Merchant expanding course catalog by 3x", "Banking cost confirmed at 1.40%", "MEDIUM RISK",
         json.dumps(["MDR reduction 11.9%"]), "CHECKER_REVIEW", "CHECKER", "IN_PROGRESS",
         (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=36)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 5. BANKING_MARGIN_VALIDATION
        ("PR-2026-0005", "MERCH-1004", "Cards", 1.75, 1.50, 0.0, 0.0, "2026-04-01", "Multi-year SaaS agreement pricing", 120000000.0,
         "Neha Sen", "SaaS client agreeing to 3-year lock-in", "Pending network fee confirmation from HDFC", "MEDIUM RISK",
         json.dumps(["MDR reduction 14.3%"]), "BANKING_MARGIN_VALIDATION", "CHECKER", "IN_PROGRESS",
         (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=44)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 6. POC_REVIEW
        ("PR-2026-0006", "MERCH-1006", "Cards", 1.90, 1.75, 0.0, 0.0, "2026-04-10", "Airline summer booking seasonal discount", 95000000.0,
         "Rahul Verma", "Seasonal incentive program for q2 flight bookings", "Valid for 6 months only", "LOW RISK",
         json.dumps(["MDR reduction 7.9%"]), "POC_REVIEW", "STANDARD", "IN_PROGRESS",
         (base_time - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 7. INITIAL_VALIDATION
        ("PR-2026-0007", "MERCH-1008", "Cards", 1.95, 1.75, 1.0, 0.5, "2026-04-05", "Franchise network expansion discount", 34000000.0,
         "Siddharth Rao", "Food delivery aggregator adding 400 new cloud kitchens", "Requires POC sign-off", "LOW RISK",
         json.dumps(["MDR reduction 10.2%"]), "INITIAL_VALIDATION", "CHECKER", "IN_PROGRESS",
         (base_time - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=43)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 8. DRAFT (Just created)
        ("PR-2026-0008", "MERCH-1007", "Cards", 2.20, 1.90, 3.0, 2.0, "2026-04-15", "Diagnostic center network onboarding", 18000000.0,
         "Siddharth Rao", "Drafting proposal for diagnostic chain", "Work in progress", "MEDIUM RISK",
         json.dumps(["Draft request"]), "DRAFT", "CHECKER", "DRAFT",
         (base_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=46)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 9. REJECTED (Negative Margin / Loss making)
        ("PR-2026-0009", "MERCH-1009", "Cards", 2.40, 0.90, 5.0, 0.0, "2026-03-01", "Aggressive SMB acquiring bid", 4500000.0,
         "Karan Mehta", "Attempted to capture SMB retail market share", "Bank cost is 1.25%, proposed MDR 0.90% leads to negative margin", "CRITICAL",
         json.dumps(["Projected Gross Margin -0.35% (Negative / Below 0%)", "BLOCKED by Policy"]), "REJECTED", "FUNCTION_HEAD", "REJECTED",
         (base_time - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 10. SENT_BACK (Missing documentation / justification)
        ("PR-2026-0010", "MERCH-1010", "UPI Recurring", 0.18, 0.08, 4.5, 2.0, "2026-03-10", "OTT subscription push", 48000000.0,
         "Karan Mehta", "Lower UPI fees to drive auto-debit adoption", "Merchant status is Under Review - needs Risk Ops clearance", "HIGH RISK",
         json.dumps(["Merchant status Under Review", "MDR reduction 55.5%"]), "SENT_BACK", "FUNCTION_HEAD", "SENT_BACK",
         (base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 11. SLA BREACHED (Pending over 50 hours)
        ("PR-2026-0011", "MERCH-1011", "Cards", 1.70, 1.40, 0.0, 0.0, "2026-03-05", "B2B wholesale portal pricing", 175000000.0,
         "Rahul Verma", "High volume B2B distributor", "Stuck in Banking Ops review due to missing ICICI rate card", "HIGH RISK",
         json.dumps(["MDR reduction 17.6%", "SLA Breached (>48h)"]), "BANKING_MARGIN_VALIDATION", "CHECKER", "IN_PROGRESS",
         (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S"), 1),

        # 12. EXECUTED (UPI Recurring)
        ("PR-2026-0012", "MERCH-1004", "UPI Recurring", 0.12, 0.10, 3.5, 3.0, "2026-02-01", "SaaS recurring payment revamp", 120000000.0,
         "Neha Sen", "Optimize SaaS mandate success rates", "Approved by Banking and Checker", "LOW RISK",
         json.dumps(["Standard UPI optimization"]), "READY_FOR_EXECUTION", "STANDARD", "EXECUTED",
         (base_time - timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=18)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=18)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 13. EXECUTED (E-Mandate)
        ("PR-2026-0013", "MERCH-1012", "E-Mandate", 0.0, 0.0, 10.0, 8.0, "2026-02-15", "BFSI auto-debit volume fee cut", 140000000.0,
         "Neha Sen", "Insurance premium monthly payment fee reduction", "Approved by Checker", "LOW RISK",
         json.dumps(["Fixed fee reduction 20%"]), "READY_FOR_EXECUTION", "STANDARD", "EXECUTED",
         (base_time - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 14. EXECUTED (Optimiser)
        ("PR-2026-0014", "MERCH-1001", "Optimiser", 0.05, 0.03, 1.5, 1.0, "2026-02-20", "Smart routing platform bundling", 150000000.0,
         "Rahul Verma", "Bundled package with core Cards processing", "Approved by Checker", "LOW RISK",
         json.dumps(["Optimiser platform discount"]), "READY_FOR_EXECUTION", "STANDARD", "EXECUTED",
         (base_time - timedelta(days=12)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=11)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=11)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 15. CHECKER_REVIEW (High GMV merchant)
        ("PR-2026-0015", "MERCH-1014", "Cards", 2.00, 1.70, 2.0, 1.0, "2026-04-01", "Real estate portal launch", 28000000.0,
         "Siddharth Rao", "Special launching promo pricing", "Requires Checker validation", "MEDIUM RISK",
         json.dumps(["MDR reduction 15.0%"]), "CHECKER_REVIEW", "CHECKER", "IN_PROGRESS",
         (base_time - timedelta(days=1, hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=32)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 16. BANKING_MARGIN_VALIDATION (UPI Recurring)
        ("PR-2026-0016", "MERCH-1003", "UPI Recurring", 0.20, 0.15, 5.0, 4.0, "2026-04-01", "Student subscription payment tier", 22000000.0,
         "Siddharth Rao", "Recurring tuition payment discount", "Awaiting NPCI fee assessment", "LOW RISK",
         json.dumps(["MDR reduction 25.0%"]), "BANKING_MARGIN_VALIDATION", "FUNCTION_HEAD", "IN_PROGRESS",
         (base_time - timedelta(hours=22)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=26)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 17. POC_REVIEW
        ("PR-2026-0017", "MERCH-1008", "Optimiser", 0.04, 0.02, 1.0, 0.5, "2026-04-05", "Multi-acquirer routing trial", 34000000.0,
         "Priya Nair", "Add Optimiser smart gateway selector", "Trial phase 90 days", "LOW RISK",
         json.dumps(["Optimiser fee reduction"]), "POC_REVIEW", "STANDARD", "IN_PROGRESS",
         (base_time - timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=34)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 18. REJECTED (Merchant Suspended)
        ("PR-2026-0018", "MERCH-1013", "Cards", 2.50, 1.95, 5.0, 2.0, "2026-03-01", "Account reinstatement attempt", 3200000.0,
         "Karan Mehta", "Requested fee cut to restart operations", "Merchant account is Suspended by Compliance", "CRITICAL",
         json.dumps(["Merchant status Suspended", "BLOCKED by Policy"]), "REJECTED", "FUNCTION_HEAD", "REJECTED",
         (base_time - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 19. READY_FOR_EXECUTION
        ("PR-2026-0019", "MERCH-1006", "E-Mandate", 0.0, 0.0, 15.0, 12.0, "2026-03-25", "Travel subscription EMandate rate", 95000000.0,
         "Rahul Verma", "Frequent flyer auto-renewals", "Checker approved", "LOW RISK",
         json.dumps(["Fixed fee discount"]), "READY_FOR_EXECUTION", "STANDARD", "APPROVED",
         (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=28)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 20. INITIAL_VALIDATION
        ("PR-2026-0020", "MERCH-1002", "UPI Recurring", 0.15, 0.10, 4.0, 3.0, "2026-04-10", "Gaming pass auto-renewal fee cut", 85000000.0,
         "Neha Sen", "Monthly battlepass recurring subscription", "Initial submission", "LOW RISK",
         json.dumps(["MDR reduction 33.3%"]), "INITIAL_VALIDATION", "FUNCTION_HEAD", "IN_PROGRESS",
         (base_time - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=45)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 21. FUNCTION_HEAD_APPROVAL (At Risk SLA)
        ("PR-2026-0021", "MERCH-1011", "Optimiser", 0.05, 0.01, 2.0, 0.0, "2026-03-30", "B2B platform cross-sell bundle", 175000000.0,
         "Rahul Verma", "Include zero-cost Optimiser routing for B2B portal", "High GMV merchant deep discount", "HIGH RISK",
         json.dumps(["MDR reduction 80.0%", "GMV > ₹50M"]), "FUNCTION_HEAD_APPROVAL", "FUNCTION_HEAD", "IN_PROGRESS",
         (base_time - timedelta(days=1, hours=20)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"), 0),

        # 22. DRAFT
        ("PR-2026-0022", "MERCH-1012", "Cards", 1.80, 1.55, 0.0, 0.0, "2026-04-20", "Insurance policy payment revamp", 140000000.0,
         "Priya Nair", "Drafting annual insurance premium tier", "Internal draft", "MEDIUM RISK",
         json.dumps(["MDR reduction 13.9%"]), "DRAFT", "CHECKER", "DRAFT",
         (base_time - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time + timedelta(hours=47)).strftime("%Y-%m-%d %H:%M:%S"), 0)
    ]

    cursor.executemany("""
    INSERT INTO pricing_requests (
        request_id, merchant_id, payment_method, current_mdr, proposed_mdr,
        current_fixed_fee, proposed_fixed_fee, effective_date, reason, expected_monthly_gmv,
        requestor, business_justification, supporting_notes, risk_level, risk_reasons,
        current_stage, required_approval_level, status, created_at, updated_at,
        sla_deadline, is_sla_breached
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, requests_data)

    # 5. Seed Banking Cost Assumptions for requests past Initial Validation
    banking_costs_data = [
        ("PR-2026-0001", 1.10, 0.35, 0.05, 0.02, "Standard HDFC Visa Interchange rate card", "Banking Ops", (base_time - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0002", 1.05, 0.30, 0.05, 0.02, "Special ICICI Enterprise tier rate confirmed", "Banking Ops", (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0003", 0.95, 0.22, 0.03, 0.01, "Compressed Interchange agreed with Axis Bank", "Banking Ops", (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0004", 1.20, 0.35, 0.05, 0.02, "Standard MasterCard Interchange card", "Banking Ops", (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0005", 1.00, 0.30, 0.04, 0.01, "HDFC Direct Bind pricing confirmed", "Banking Ops", (base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0009", 0.90, 0.30, 0.04, 0.01, "Interchange 0.90% equal to proposed MDR", "Banking Ops", (base_time - timedelta(days=6, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0011", 0.95, 0.30, 0.04, 0.01, "Incomplete bank NOC", "Banking Ops", (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0015", 1.15, 0.35, 0.05, 0.02, "Kotak Mahindra rate card verified", "Banking Ops", (base_time - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0016", 0.05, 0.04, 0.50, 0.10, "NPCI UPI mandate transaction cost", "Banking Ops", (base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0019", 0.00, 0.00, 3.50, 0.50, "Bank auto-debit charge INR 4.00 per mandate", "Banking Ops", (base_time - timedelta(days=1, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0021", 0.00, 0.00, 0.00, 0.00, "Optimiser routing software server cost negligible", "Banking Ops", (base_time - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    cursor.executemany("""
    INSERT INTO banking_costs (request_id, network_cost_percent, bank_cost_percent, processing_cost_fixed, other_op_cost_fixed, notes, updated_by, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, banking_costs_data)

    # 6. Seed Approval Records
    approvals_data = [
        # PR-2026-0001
        ("PR-2026-0001", "POC_REVIEW", "Amit Roy", "POC Reviewer", "APPROVE", "Volume growth verified. Merchant qualifies for tier discount.", "Met GMV threshold", (base_time - timedelta(days=9, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0001", "BANKING_MARGIN_VALIDATION", "Smita Rao", "Banking Operations", "APPROVE", "Margin standard 0.18% preserved above threshold.", "Cost card verified", (base_time - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0001", "CHECKER_REVIEW", "Sunil Joshi", "Checker", "APPROVE", "Final operational review complete. Approved for execution.", "Standard approval complete", (base_time - timedelta(days=8, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),

        # PR-2026-0002
        ("PR-2026-0002", "POC_REVIEW", "Amit Roy", "POC Reviewer", "APPROVE", "High threat of churn confirmed by Account Manager.", "Competitive urgency", (base_time - timedelta(days=3, hours=18)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0002", "BANKING_MARGIN_VALIDATION", "Smita Rao", "Banking Operations", "APPROVE", "Special ICICI interchange card verified.", "Margin 0.25% acceptable", (base_time - timedelta(days=2, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0002", "CHECKER_REVIEW", "Sunil Joshi", "Checker", "APPROVE", "Checker review passed. Churn mitigation justified.", "Approved for execution", (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),

        # PR-2026-0003
        ("PR-2026-0003", "POC_REVIEW", "Amit Roy", "POC Reviewer", "APPROVE", "Strategic Quick Commerce anchor merchant.", "High GMV account", (base_time - timedelta(days=2, hours=20)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0003", "BANKING_MARGIN_VALIDATION", "Smita Rao", "Banking Operations", "APPROVE", "Interchange rate cut agreed with Axis Bank.", "Margin 3.8% requires Function Head approval", (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0003", "CHECKER_REVIEW", "Sunil Joshi", "Checker", "APPROVE", "Escalated to Function Head due to >20% MDR drop.", "High Risk Escalation", (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),

        # PR-2026-0009 (Rejected)
        ("PR-2026-0009", "POC_REVIEW", "Amit Roy", "POC Reviewer", "APPROVE", "Pushed by sales team.", "Pending margin test", (base_time - timedelta(days=7, hours=6)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0009", "BANKING_MARGIN_VALIDATION", "Smita Rao", "Banking Operations", "REJECT", "Proposed MDR 0.90% below banking cost 1.25%. Negative gross margin of -0.35%.", "Negative Margin / Below Policy Limit", (base_time - timedelta(days=6, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),

        # PR-2026-0010 (Sent back)
        ("PR-2026-0010", "POC_REVIEW", "Amit Roy", "POC Reviewer", "SEND BACK", "Merchant status is Under Review. Cannot approve pricing revamp without Risk clearance.", "Risk Clearance Missing", (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"))
    ]

    cursor.executemany("""
    INSERT INTO approval_history (request_id, stage, reviewer, role, decision, comments, reason, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, approvals_data)

    # 7. Seed Tickets
    tkt_comments_1 = json.dumps([
        {"author": "System", "role": "System", "timestamp": (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "message": "Ticket created automatically due to SLA breach warning."},
        {"author": "Smita Rao", "role": "Banking Operations", "timestamp": (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"), "message": "Waiting for ICICI Bank acquiring team to confirm rate card."}
    ])

    tkt_comments_2 = json.dumps([
        {"author": "System", "role": "System", "timestamp": (base_time - timedelta(days=6, hours=12)).strftime("%Y-%m-%d %H:%M:%S"), "message": "Ticket created for negative margin pricing rejection."}
    ])

    tkt_comments_3 = json.dumps([
        {"author": "Sunil Joshi", "role": "Checker", "timestamp": (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), "message": "High GMV merchant pricing change requires Function Head sign-off before 5 PM today."}
    ])

    tickets_data = [
        ("TKT-2026-0001", "PR-2026-0011", "MERCH-1011", "Banking Operations", "HIGH", "SLA Warning", "IN_PROGRESS",
         (base_time - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
         tkt_comments_1, "Pending ICICI Rate Card"),

        ("TKT-2026-0002", "PR-2026-0009", "MERCH-1009", "Pricing Operations", "CRITICAL", "Margin Review", "RESOLVED",
         (base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=6, hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S"),
         tkt_comments_2, "Pricing request rejected due to negative margin"),

        ("TKT-2026-0003", "PR-2026-0003", "MERCH-1005", "Checker Team", "HIGH", "Pending Approval", "PENDING_APPROVAL",
         (base_time + timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
         tkt_comments_3, "Awaiting Function Head sign-off"),

        ("TKT-2026-0004", "PR-2026-0010", "MERCH-1010", "Pricing Operations", "HIGH", "Policy Override", "WAITING_FOR_INPUT",
         (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
         json.dumps([{"author": "Karan Mehta", "role": "Pricing Analyst", "timestamp": (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"), "message": "Requesting Risk Ops clearance document."}]), "Waiting for merchant status update"),

        ("TKT-2026-0005", "PR-2026-0021", "MERCH-1011", "Finance", "MEDIUM", "Pricing Dispute", "OPEN",
         (base_time + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
         (base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
         json.dumps([{"author": "System", "role": "System", "timestamp": (base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"), "message": "Ticket created for zero-cost Optimiser cross-sell review."}]), "Under finance team review")
    ]

    cursor.executemany("""
    INSERT INTO tickets (ticket_id, request_id, merchant_id, assigned_team, priority, category, status, sla_due, created_at, updated_at, comments, resolution)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tickets_data)

    # 8. Seed Audit Log Events
    audit_data = [
        ("PR-2026-0001", "MERCH-1001", "Rahul Verma", "Pricing Analyst", "REQUEST_CREATED", None, "DRAFT", "New volume tier request", (base_time - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0001", "MERCH-1001", "Rahul Verma", "Pricing Analyst", "REQUEST_SUBMITTED", "DRAFT", "INITIAL_VALIDATION", "Submitted for review", (base_time - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0001", "MERCH-1001", "System", "System Engine", "VALIDATION_COMPLETED", "INITIAL_VALIDATION", "POC_REVIEW", "Validation PASS", (base_time - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0001", "MERCH-1001", "Amit Roy", "POC Reviewer", "POC_APPROVED", "POC_REVIEW", "BANKING_MARGIN_VALIDATION", "Volume tier verified", (base_time - timedelta(days=9, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0001", "MERCH-1001", "Smita Rao", "Banking Operations", "BANKING_APPROVED", "BANKING_MARGIN_VALIDATION", "CHECKER_REVIEW", "Cost card confirmed", (base_time - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0001", "MERCH-1001", "Sunil Joshi", "Checker", "CHECKER_APPROVED", "CHECKER_REVIEW", "READY_FOR_EXECUTION", "Checker approved", (base_time - timedelta(days=8, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0001", "MERCH-1001", "Sunil Joshi", "Checker", "PRICING_EXECUTED", "MDR 1.85%", "MDR 1.70%", "Applied active rate configuration in production", (base_time - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0009", "MERCH-1009", "Karan Mehta", "Pricing Analyst", "REQUEST_CREATED", None, "DRAFT", "SMB bid proposal", (base_time - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0009", "MERCH-1009", "Smita Rao", "Banking Operations", "REQUEST_REJECTED", "BANKING_MARGIN_VALIDATION", "REJECTED", "Negative margin -0.35% violates policy", (base_time - timedelta(days=6, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0010", "MERCH-1010", "Karan Mehta", "Pricing Analyst", "REQUEST_CREATED", None, "DRAFT", "OTT subscription push", (base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")),
        ("PR-2026-0010", "MERCH-1010", "Amit Roy", "POC Reviewer", "REQUEST_SENT_BACK", "POC_REVIEW", "SENT_BACK", "Merchant Under Review state requires Risk clearance", (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")),
    ]

    cursor.executemany("""
    INSERT INTO audit_logs (request_id, merchant_id, actor, actor_role, action, old_value, new_value, reason, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, audit_data)

    conn.commit()
    conn.close()
