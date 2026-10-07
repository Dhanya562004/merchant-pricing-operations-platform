"""
Data Models and Enums for Merchant Pricing Operations Platform.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class PaymentMethod(str, Enum):
    CARDS = "Cards"
    UPI_RECURRING = "UPI Recurring"
    E_MANDATE = "E-Mandate"
    OPTIMISER = "Optimiser"


class MerchantTier(str, Enum):
    ENTERPRISE = "Enterprise"
    MID_MARKET = "Mid-Market"
    SMB = "SMB"


class MerchantStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    UNDER_REVIEW = "Under Review"


class RiskLevel(str, Enum):
    LOW = "LOW RISK"
    MEDIUM = "MEDIUM RISK"
    HIGH = "HIGH RISK"
    CRITICAL = "CRITICAL"


class WorkflowStage(str, Enum):
    DRAFT = "DRAFT"
    INITIAL_VALIDATION = "INITIAL_VALIDATION"
    POC_REVIEW = "POC_REVIEW"
    BANKING_MARGIN_VALIDATION = "BANKING_MARGIN_VALIDATION"
    CHECKER_REVIEW = "CHECKER_REVIEW"
    FUNCTION_HEAD_APPROVAL = "FUNCTION_HEAD_APPROVAL"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    SENT_BACK = "SENT_BACK"


class ApprovalLevel(str, Enum):
    STANDARD = "STANDARD"
    CHECKER = "CHECKER"
    FUNCTION_HEAD = "FUNCTION_HEAD"


class Decision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SEND_BACK = "SEND BACK"


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class UserRole(str, Enum):
    PRICING_ANALYST = "Pricing Analyst"
    POC_REVIEWER = "POC Reviewer"
    BANKING_OPS = "Banking Operations"
    CHECKER = "Checker"
    FUNCTION_HEAD = "Function Head"
    OPERATIONS_ADMIN = "Operations Admin"


@dataclass
class Merchant:
    merchant_id: str
    merchant_name: str
    industry: str
    merchant_tier: str
    monthly_gmv: float
    transaction_count: int
    current_status: str
    account_manager: str
    risk_category: str


@dataclass
class PricingConfig:
    id: Optional[int]
    merchant_id: str
    payment_method: str
    mdr_percent: float
    fixed_fee: float
    minimum_fee: float
    maximum_fee: float
    effective_from: str
    effective_to: Optional[str]
    pricing_status: str
    last_updated_by: str
    last_updated_at: str


@dataclass
class PricingRequest:
    request_id: str
    merchant_id: str
    payment_method: str
    current_mdr: float
    proposed_mdr: float
    current_fixed_fee: float
    proposed_fixed_fee: float
    effective_date: str
    reason: str
    expected_monthly_gmv: float
    requestor: str
    business_justification: str
    supporting_notes: str
    risk_level: str
    risk_reasons: List[str]
    current_stage: str
    required_approval_level: str
    status: str
    created_at: str
    updated_at: str
    sla_deadline: str
    is_sla_breached: bool = False


@dataclass
class BankingCost:
    id: Optional[int]
    request_id: str
    network_cost_percent: float
    bank_cost_percent: float
    processing_cost_fixed: float
    other_op_cost_fixed: float
    notes: str
    updated_by: str
    updated_at: str


@dataclass
class ApprovalRecord:
    id: Optional[int]
    request_id: str
    stage: str
    reviewer: str
    role: str
    decision: str
    comments: str
    reason: str
    created_at: str


@dataclass
class Ticket:
    ticket_id: str
    request_id: str
    merchant_id: str
    assigned_team: str
    priority: str
    category: str
    status: str
    sla_due: str
    created_at: str
    updated_at: str
    comments: List[Dict[str, Any]]
    resolution: str


@dataclass
class AuditEvent:
    event_id: Optional[int]
    request_id: str
    merchant_id: str
    actor: str
    actor_role: str
    action: str
    old_value: str
    new_value: str
    reason: str
    timestamp: str


@dataclass
class ValidationResult:
    status: str  # PASS, WARNING, BLOCKED
    rules_checked: List[Dict[str, Any]]
    is_eligible: bool
    summary_message: str
