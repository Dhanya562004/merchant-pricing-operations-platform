"""
Database connection and schema initialization for Merchant Pricing Operations Platform.
"""
import sqlite3
import os
import json
from typing import Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pricing_ops.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory enabled."""
    target_db = db_path or DB_FILE
    conn = sqlite3.connect(target_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes SQLite database tables if they do not exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Create merchants table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merchants (
        merchant_id TEXT PRIMARY KEY,
        merchant_name TEXT NOT NULL,
        industry TEXT NOT NULL,
        merchant_tier TEXT NOT NULL,
        monthly_gmv REAL NOT NULL,
        transaction_count INTEGER NOT NULL,
        current_status TEXT NOT NULL,
        account_manager TEXT NOT NULL,
        risk_category TEXT NOT NULL
    )
    """)

    # Create merchant pricing configuration table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merchant_pricing_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        merchant_id TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        mdr_percent REAL NOT NULL,
        fixed_fee REAL NOT NULL,
        minimum_fee REAL NOT NULL,
        maximum_fee REAL NOT NULL,
        effective_from TEXT NOT NULL,
        effective_to TEXT,
        pricing_status TEXT NOT NULL,
        last_updated_by TEXT NOT NULL,
        last_updated_at TEXT NOT NULL,
        FOREIGN KEY (merchant_id) REFERENCES merchants (merchant_id)
    )
    """)

    # Create pricing requests table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pricing_requests (
        request_id TEXT PRIMARY KEY,
        merchant_id TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        current_mdr REAL NOT NULL,
        proposed_mdr REAL NOT NULL,
        current_fixed_fee REAL NOT NULL,
        proposed_fixed_fee REAL NOT NULL,
        effective_date TEXT NOT NULL,
        reason TEXT NOT NULL,
        expected_monthly_gmv REAL NOT NULL,
        requestor TEXT NOT NULL,
        business_justification TEXT NOT NULL,
        supporting_notes TEXT,
        risk_level TEXT NOT NULL,
        risk_reasons TEXT NOT NULL,
        current_stage TEXT NOT NULL,
        required_approval_level TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        sla_deadline TEXT NOT NULL,
        is_sla_breached INTEGER DEFAULT 0,
        FOREIGN KEY (merchant_id) REFERENCES merchants (merchant_id)
    )
    """)

    # Create banking costs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS banking_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT UNIQUE NOT NULL,
        network_cost_percent REAL NOT NULL,
        bank_cost_percent REAL NOT NULL,
        processing_cost_fixed REAL NOT NULL,
        other_op_cost_fixed REAL NOT NULL,
        notes TEXT,
        updated_by TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (request_id) REFERENCES pricing_requests (request_id)
    )
    """)

    # Create approval history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approval_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT NOT NULL,
        stage TEXT NOT NULL,
        reviewer TEXT NOT NULL,
        role TEXT NOT NULL,
        decision TEXT NOT NULL,
        comments TEXT,
        reason TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (request_id) REFERENCES pricing_requests (request_id)
    )
    """)

    # Create tickets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL,
        merchant_id TEXT NOT NULL,
        assigned_team TEXT NOT NULL,
        priority TEXT NOT NULL,
        category TEXT NOT NULL,
        status TEXT NOT NULL,
        sla_due TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        comments TEXT NOT NULL,
        resolution TEXT
    )
    """)

    # Create audit logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT,
        merchant_id TEXT,
        actor TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        action TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        reason TEXT,
        timestamp TEXT NOT NULL
    )
    """)

    # Create policy config table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policy_config (
        policy_key TEXT PRIMARY KEY,
        policy_name TEXT NOT NULL,
        value REAL NOT NULL,
        description TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def reset_database(db_path: Optional[str] = None) -> None:
    """Resets database and re-seeds original demo dataset."""
    from src.seed_data import seed_all_data
    target_db = db_path or DB_FILE
    if os.path.exists(target_db):
        try:
            os.remove(target_db)
        except Exception:
            # If open by active connection, drop all tables
            conn = get_connection(target_db)
            cursor = conn.cursor()
            tables = ["audit_logs", "tickets", "approval_history", "banking_costs", 
                      "pricing_requests", "merchant_pricing_config", "merchants", "policy_config"]
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
            conn.close()

    init_db(target_db)
    seed_all_data(target_db)
