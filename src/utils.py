"""
Utility and Formatting functions for Merchant Pricing Operations Platform.
Provides currency/percentage formatting, custom HTML badge generators, and sleek CSS styling.
"""
import streamlit as st


def format_inr(amount: float) -> str:
    """Formats numeric amounts into Indian Rupee (INR) currency format."""
    if amount is None:
        return "₹0.00"
    
    val = float(amount)
    is_negative = val < 0
    val = abs(val)

    # Convert to Indian numbering system formatting
    s = f"{val:.2f}"
    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        other_digits = integer_part[:-3]
        res = ""
        while len(other_digits) > 2:
            res = "," + other_digits[-2:] + res
            other_digits = other_digits[:-2]
        res = other_digits + res + "," + last_three
    else:
        res = integer_part

    formatted = f"₹{res}.{decimal_part}"
    return f"-{formatted}" if is_negative else formatted


def format_inr_short(amount: float) -> str:
    """Short format for large Indian currency amounts (Lakh / Crore)."""
    if amount is None:
        return "₹0"
    val = float(amount)
    abs_val = abs(val)
    prefix = "-" if val < 0 else ""

    if abs_val >= 10000000: # 1 Crore
        return f"{prefix}₹{abs_val / 10000000:.2f} Cr"
    elif abs_val >= 100000: # 1 Lakh
        return f"{prefix}₹{abs_val / 100000:.2f} L"
    else:
        return f"{prefix}₹{abs_val:,.0f}"


def format_pct(val: float) -> str:
    """Formats float as percentage string."""
    if val is None:
        return "0.00%"
    return f"{float(val):.2f}%"


def get_risk_badge(risk_level: str) -> str:
    """Returns styled HTML badge for risk classification."""
    colors = {
        "LOW RISK": ("#10b981", "rgba(16, 185, 129, 0.15)"),
        "MEDIUM RISK": ("#f59e0b", "rgba(245, 158, 11, 0.15)"),
        "HIGH RISK": ("#ef4444", "rgba(239, 68, 68, 0.15)"),
        "CRITICAL": ("#dc2626", "rgba(220, 38, 38, 0.25)"),
    }
    fg, bg = colors.get(risk_level, ("#6b7280", "rgba(107, 114, 128, 0.15)"))
    return f'<span style="background-color: {bg}; color: {fg}; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid {fg}; font-size: 0.8rem; display: inline-block;">{risk_level}</span>'


def get_status_badge(status: str) -> str:
    """Returns styled HTML badge for workflow status."""
    colors = {
        "EXECUTED": ("#10b981", "rgba(16, 185, 129, 0.15)"),
        "APPROVED": ("#10b981", "rgba(16, 185, 129, 0.15)"),
        "IN_PROGRESS": ("#3b82f6", "rgba(59, 130, 246, 0.15)"),
        "DRAFT": ("#6b7280", "rgba(107, 114, 128, 0.15)"),
        "REJECTED": ("#ef4444", "rgba(239, 68, 68, 0.15)"),
        "SENT_BACK": ("#f59e0b", "rgba(245, 158, 11, 0.15)"),
        "OPEN": ("#3b82f6", "rgba(59, 130, 246, 0.15)"),
        "WAITING_FOR_INPUT": ("#8b5cf6", "rgba(139, 92, 246, 0.15)"),
        "PENDING_APPROVAL": ("#f59e0b", "rgba(245, 158, 11, 0.15)"),
        "RESOLVED": ("#10b981", "rgba(16, 185, 129, 0.15)"),
        "CLOSED": ("#6b7280", "rgba(107, 114, 128, 0.15)")
    }
    fg, bg = colors.get(status, ("#6b7280", "rgba(107, 114, 128, 0.15)"))
    return f'<span style="background-color: {bg}; color: {fg}; font-weight: 600; padding: 3px 8px; border-radius: 4px; border: 1px solid {fg}; font-size: 0.78rem; display: inline-block;">{status}</span>'


def get_sla_badge(sla_status: str, time_str: str = "") -> str:
    """Returns styled SLA status badge with icon."""
    if sla_status == "BREACHED":
        return f'<span style="background-color: rgba(239, 68, 68, 0.15); color: #ef4444; font-weight: 600; padding: 4px 8px; border-radius: 6px; border: 1px solid #ef4444; font-size: 0.78rem;">🔴 Breached ({time_str})</span>'
    elif sla_status == "AT_RISK":
        return f'<span style="background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; font-weight: 600; padding: 4px 8px; border-radius: 6px; border: 1px solid #f59e0b; font-size: 0.78rem;">🟡 At Risk ({time_str})</span>'
    elif sla_status == "OK" or sla_status == "COMPLETED" or sla_status == "RESOLVED":
        return f'<span style="background-color: rgba(16, 185, 129, 0.15); color: #10b981; font-weight: 600; padding: 4px 8px; border-radius: 6px; border: 1px solid #10b981; font-size: 0.78rem;">🟢 Within SLA</span>'
    else:
        return f'<span style="background-color: rgba(107, 114, 128, 0.15); color: #9ca3af; font-weight: 600; padding: 4px 8px; border-radius: 6px; border: 1px solid #9ca3af; font-size: 0.78rem;">⚪ {time_str or "N/A"}</span>'


def inject_custom_css():
    """Injects ultra-sleek, modern dark-mode fintech ops console styling into Streamlit UI."""
    css = """
    <style>
    /* Main Layout & Dark Glassmorphic Theme */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Header Bar */
    .app-header {
        background: linear-gradient(135deg, #161b22 0%, #1f2937 100%);
        padding: 18px 24px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 24px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    .app-header h1 {
        color: #f0f6fc;
        font-size: 1.6rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .app-header p {
        color: #8b949e;
        font-size: 0.9rem;
        margin: 4px 0 0 0;
    }
    
    /* Metric KPI Cards */
    .kpi-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-card:hover {
        border-color: #58a6ff;
        transform: translateY(-2px);
    }
    .kpi-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8b949e;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #f0f6fc;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #8b949e;
        margin-top: 4px;
    }

    /* Section Cards */
    .section-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }

    /* Streamlit Metric Overrides */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #58a6ff !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #8b949e !important;
        font-weight: 600 !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161b22;
        padding: 6px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        border-radius: 6px;
        color: #8b949e;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262d !important;
        color: #f0f6fc !important;
        border: 1px solid #58a6ff !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d !important;
    }

    /* Form Container */
    [data-testid="stForm"] {
        border: 1px solid #30363d;
        background: #161b22;
        border-radius: 12px;
        padding: 20px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
