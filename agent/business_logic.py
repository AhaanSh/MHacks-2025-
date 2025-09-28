"""
business_logic.py

- In-memory per-user context (resets on process restart)
- Reset/clear filters detection and handling
- Robust parsing/merging of filters
- Operator support for bedrooms/bathrooms
- Property type filtering (house, apartment, etc.)
- Drops NaN rows for actively-filtered columns
- Deduplicates by id (or address if id missing)
- Clean formatted output (no 'nan'), agent -> office fallback
- City/state parsing + normalization (state names -> abbreviations)
"""
import os
import re
from typing import Any, Dict, Optional

import pandas as pd

# --- Load CSV ---
CSV_PATH = os.path.join(os.path.dirname(__file__), "rentals.csv")
try:
    rentals_df = pd.read_csv(CSV_PATH)
except Exception as e:
    rentals_df = pd.DataFrame()
    print(f"Error loading rentals.csv: {e}")

# --- In-memory per-user context (resets when process restarts) ---
user_context: Dict[str, Dict[str, Any]] = {}

# --- State map for name -> abbreviation ---
STATE_MAP = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI",
    "south carolina": "SC", "south dakota": "SD", "tennessee": "TN",
    "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA",
    "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY"
}


# ---------------- Helpers ----------------
def parse_number(value: Any) -> Optional[float]:
    """Parse numbers like '500000', '$500k', '1M', '2.5', 3 -> returns numeric or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().lower()
    if s == "":
        return None
    s = s.replace("$", "").replace(" ", "").replace(",", "")
    multiplier = 1.0
    if s.endswith("k"):
        multiplier = 1_000.0
        s = s[:-1]
    elif s.endswith("m"):
        multiplier = 1_000_000.0
        s = s[:-1]
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if not m:
        return None
    try:
        return float(m.group(0)) * multiplier
    except Exception:
        return None


def normalize_operator(op: Optional[str]) -> Optional[str]:
    """Normalize various operator strings to one of: '>=', '<=', '>', '<', '==' or None."""
    if op is None:
        return None
    op_s = str(op).strip().lower()
    if op_s in {">=", "gte", "greaterorequal", "at least", "atleast", "minimum", "min"}:
        return ">="
    if op_s in {"<=", "lte", "lessorequal", "at most", "atmost", "maximum", "max"}:
        return "<="
    if op_s in {">", "gt", "more than", "greater than", "above"}:
        return ">"
    if op_s in {"<", "lt", "less than", "below"}:
        return "<"
    if op_s in {"=", "==", "eq", "exactly"}:
        return "=="
    if "at least" in op_s:
        return ">="
    if "at most" in op_s:
        return "<="
    return None


def apply_operator_filter(df: pd.DataFrame, col: str, value: Optional[float], operator: Optional[str]) -> pd.DataFrame:
    """Apply numeric operator filter safely. If operator is None => >= by default."""
    if value is None or col not in df.columns:
        return df
    op = normalize_operator(operator) or ">="
    try:
        if op == ">=":
            return df[df[col] >= value]
        if op == "<=":
            return df[df[col] <= value]
        if op == ">":
            return df[df[col] > value]
        if op == "<":
            return df[df[col] < value]
        if op == "==":
            return df[df[col] == value]
    except Exception:
        return df
    return df


def pretty_price(val: Any) -> str:
    """Return nicely formatted price or raw fallback."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    try:
        num = int(float(val))
        return f"${num:,}"
    except Exception:
        return str(val)


def clean_value(val: Any) -> Optional[str]:
    """Return None when NaN/empty, otherwise stringified value."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None
    return s


def build_contact_info(row: Dict[str, Any]) -> Optional[str]:
    """
    Prefer agent info, fallback to office info. Return joined string or None.
    Expected fields in CSV: agent_name, agent_phone, agent_email, office_name, office_phone, office_email
    """
    parts = []
    if row.get("agent_name"):
        parts.append(str(row["agent_name"]).strip())
    if row.get("agent_phone") and str(row["agent_phone"]).lower() != "nan":
        parts.append(str(row["agent_phone"]).strip())
    if row.get("agent_email") and str(row["agent_email"]).lower() != "nan":
        parts.append(str(row["agent_email"]).strip())

    if parts:
        return ", ".join(parts)

    office_parts = []
    if row.get("office_name"):
        office_parts.append(str(row["office_name"]).strip())
    if row.get("office_phone") and str(row["office_phone"]).lower() != "nan":
        office_parts.append(str(row["office_phone"]).strip())
    if row.get("office_email") and str(row["office_email"]).lower() != "nan":
        office_parts.append(str(row["office_email"]).strip())

    if office_parts:
        return ", ".join(office_parts)

    return None


def summarize_filters(filters: Dict[str, Any]) -> str:
    """Return a human-friendly one-line description of active filters."""
    pieces = []
    if not filters:
        return "No active filters"
    if filters.get("location"):
        pieces.append(f"Location: {filters['location']}")
    if filters.get("city"):
        pieces.append(f"City: {filters['city']}")
    if filters.get("state"):
        pieces.append(f"State: {filters['state']}")
    if filters.get("budget_min") is not None:
        pieces.append(f"Min budget: {pretty_price(filters['budget_min'])}")
    if filters.get("budget_max") is not None:
        pieces.append(f"Max budget: {pretty_price(filters['budget_max'])}")
    if filters.get("bedrooms") is not None:
        op = normalize_operator(filters.get("bedroom_operator")) or ">="
        pieces.append(f"Bedrooms {op} {int(float(filters['bedrooms']))}")
    if filters.get("bathrooms") is not None:
        op = normalize_operator(filters.get("bathroom_operator")) or ">="
        pieces.append(f"Bathrooms {op} {int(float(filters['bathrooms']))}")
    if filters.get("property_type"):
        pieces.append(f"Type: {filters['property_type']}")
    return ", ".join(pieces) if pieces else "No active filters"


def _is_reset_command_text(text: str) -> bool:
    """Return True if text contains a reset/clear instruction."""
    if not text:
        return False
    t = text.lower()
    # Multi-word phrases first to reduce false positives
    phrases = [
        "reset filters", "clear filters", "reset search", "clear search",
        "start over", "clear all filters", "clear all", "reset all filters"
    ]
    for p in phrases:
        if p in t:
            return True
    return False


# ---------------- Main handlers ----------------
def handle_user_query(sender: str, understood_query: Dict[str, Any]) -> str:
    """
    Entry point. Maintains per-user context and merges incoming filter info.
    Detects reset commands and clears context for the sender when requested.
    """
    original_message = understood_query.get("original_query", "") or ""
    llm_analysis = understood_query.get("llm_analysis", {}) or {}

    # initialize context for sender if missing
    if sender not in user_context:
        user_context[sender] = {}

    # 1) Reset detection from plain text (fast)
    if _is_reset_command_text(original_message):
        user_context[sender] = {}
        return "Your search filters have been reset."

    # 2) Reset detection from LLM analysis if it explicitly signals reset
    if isinstance(llm_analysis, dict):
        if llm_analysis.get("intent") == "reset":
            user_context[sender] = {}
            return "Your search filters have been reset."
        # also accept key_info.reset = true (if your prompt includes such a flag)
        k = llm_analysis.get("key_info", {})
        if isinstance(k, dict) and k.get("reset") in (True, "true", "yes", 1):
            user_context[sender] = {}
            return "Your search filters have been reset."

    # 3) If the LLM indicates a property_search, merge and run it
    if isinstance(llm_analysis, dict) and llm_analysis.get("intent") == "property_search":
        prev = user_context.get(sender, {}) or {}
        incoming = llm_analysis.get("key_info", {}) or {}

        # Parse numeric and operator values
        parsed_incoming: Dict[str, Any] = {}
        if "budget_min" in incoming:
            parsed_incoming["budget_min"] = parse_number(incoming.get("budget_min"))
        if "budget_max" in incoming:
            parsed_incoming["budget_max"] = parse_number(incoming.get("budget_max"))
        if "bedrooms" in incoming:
            parsed_incoming["bedrooms"] = parse_number(incoming.get("bedrooms"))
        if "bathrooms" in incoming:
            parsed_incoming["bathrooms"] = parse_number(incoming.get("bathrooms"))
        if "bedroom_operator" in incoming and incoming.get("bedroom_operator") is not None:
            parsed_incoming["bedroom_operator"] = normalize_operator(incoming.get("bedroom_operator"))
        if "bathroom_operator" in incoming and incoming.get("bathroom_operator") is not None:
            parsed_incoming["bathroom_operator"] = normalize_operator(incoming.get("bathroom_operator"))
        if "city" in incoming and incoming.get("city"):
            parsed_incoming["city"] = incoming.get("city")
        if "state" in incoming and incoming.get("state"):
            # normalize to abbreviation if possible (LLM may output full name)
            st = str(incoming.get("state")).strip()
            st_abbr = STATE_MAP.get(st.lower(), None)
            parsed_incoming["state"] = st_abbr or st.upper()
        if "location" in incoming and incoming.get("location"):
            parsed_incoming["location"] = incoming.get("location")
        if "property_type" in incoming and incoming.get("property_type"):
            parsed_incoming["property_type"] = incoming.get("property_type")

        # Merge into previous context (overwrite only with non-None incoming)
        merged = prev.copy()
        for k, v in parsed_incoming.items():
            if v is not None:
                merged[k] = v

        # Save context
        user_context[sender] = merged

        # Run rental query with merged filters
        return _run_rental_query(sender, merged)

    # 4) Fallback simple intent handling (pricing/book/ support etc.)
    msg_lower = original_message.lower()
    if any(k in msg_lower for k in ["price", "cost", "how much"]):
        return handle_pricing_query(original_message, llm_analysis)
    if any(k in msg_lower for k in ["book", "schedule", "appointment"]):
        return handle_booking_query(original_message, llm_analysis)
    if any(k in msg_lower for k in ["problem", "issue", "complaint", "not working"]):
        return handle_support_query(original_message, llm_analysis)
    if isinstance(llm_analysis, dict) and llm_analysis.get("urgency") == "high":
        return handle_urgent_query(original_message, llm_analysis)

    return handle_general_query(original_message, llm_analysis)


def _run_rental_query(sender: str, filters: Dict[str, Any]) -> str:
    """
    Perform DataFrame filtering using 'filters' that came from or are stored in context.
    """
    df = rentals_df.copy()

    # ensure numeric columns are numeric
    for c in ["price", "bedrooms", "bathrooms"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Drop rows missing required values for active filters
    if filters.get("budget_min") is not None or filters.get("budget_max") is not None:
        if "price" in df.columns:
            df = df.dropna(subset=["price"])
    if filters.get("bedrooms") is not None:
        if "bedrooms" in df.columns:
            df = df.dropna(subset=["bedrooms"])
    if filters.get("bathrooms") is not None:
        if "bathrooms" in df.columns:
            df = df.dropna(subset=["bathrooms"])

    # Apply budget
    if filters.get("budget_min") is not None and "price" in df.columns:
        df = df[df["price"] >= float(filters["budget_min"])]
    if filters.get("budget_max") is not None and "price" in df.columns:
        df = df[df["price"] <= float(filters["budget_max"])]

    # Apply bedroom/bathroom operator filters
    df = apply_operator_filter(df, "bedrooms", filters.get("bedrooms"), filters.get("bedroom_operator"))
    df = apply_operator_filter(df, "bathrooms", filters.get("bathrooms"), filters.get("bathroom_operator"))

    # propertyType filter
    if filters.get("property_type") and "propertyType" in df.columns:
        df = df[df["propertyType"].astype(str).str.contains(str(filters["property_type"]), case=False, na=False)]

    # Location: prefer explicit city/state fields if present in context
    if filters.get("city") and "city" in df.columns:
        df = df[df["city"].astype(str).str.contains(str(filters["city"]), case=False, na=False)]

    if filters.get("state") and "state" in df.columns:
        # State in context should already be abbreviation from merging stage
        desired_state = str(filters["state"]).upper()
        df = df[df["state"].astype(str).str.upper() == desired_state]

    # Fallback: tokenized location matching across city/state/formattedAddress
    if (not filters.get("city") and not filters.get("state")) and filters.get("location"):
        loc = str(filters["location"])
        tokens = [t.strip() for t in re.split(r"[, ]+", loc) if t.strip()]
        if tokens:
            cond = None
            for token in tokens:
                token_conds = []
                for col in ["state", "city", "formattedAddress"]:
                    if col in df.columns:
                        token_conds.append(df[col].astype(str).str.contains(token, case=False, na=False))
                if token_conds:
                    token_match = pd.concat(token_conds, axis=1).any(axis=1)
                    cond = token_match if cond is None else (cond & token_match)
            if cond is not None:
                df = df[cond]

    # If nothing left
    if df.empty:
        return "Sorry, I couldn’t find any properties matching your request. (Active filters: " + summarize_filters(filters) + ")"

    # Deduplicate by id or address
    if "id" in df.columns:
        df = df.drop_duplicates(subset=["id"])
    elif "formattedAddress" in df.columns:
        df = df.drop_duplicates(subset=["formattedAddress"])

    # Sort by price (if available)
    if "price" in df.columns:
        df = df.sort_values(by="price", ascending=True)

    # Format top results
    results = df.head(5).to_dict(orient="records")
    lines = [f"Here are some properties that match your request (Active filters: {summarize_filters(filters)}):\n"]

    for row in results:
        address = clean_value(row.get("formattedAddress")) or row.get("addressLine1") or row.get("city") or "Unknown"
        price_val = row.get("price")
        bedrooms_val = row.get("bedrooms")
        bathrooms_val = row.get("bathrooms")

        parts = [f"- {address}"]
        if pd.notna(price_val):
            parts.append(pretty_price(price_val))

        br_parts = []
        if pd.notna(bedrooms_val):
            try:
                br_parts.append(f"{int(bedrooms_val)} bed")
            except Exception:
                br_parts.append(f"{bedrooms_val} bed")
        if pd.notna(bathrooms_val):
            try:
                br_parts.append(f"{int(bathrooms_val)} bath")
            except Exception:
                br_parts.append(f"{bathrooms_val} bath")
        if br_parts:
            parts.append("| " + " / ".join(br_parts))

        contact = build_contact_info(row)
        if contact:
            parts.append("| Contact: " + contact)

        lines.append(" ".join(parts))

    return "\n".join(lines)


# --- Other simple handlers (unchanged) ---
def handle_pricing_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "For pricing information, I can connect you with our sales team or you can visit our pricing page. What specific product are you interested in?"


def handle_booking_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "I'd be happy to help you schedule something. Could you let me know what type of appointment you need and your preferred dates?"


def handle_support_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "I'm sorry you're experiencing an issue. Let me help you with that. Can you provide more details about what's happening?"


def handle_urgent_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "I understand this is urgent. Let me escalate this right away and get you immediate assistance."


def handle_general_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "I'm here to help! Could you provide a bit more detail about what you're looking for?"


def custom_function_example(data: Any):
    pass
