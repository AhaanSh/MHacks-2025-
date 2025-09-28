"""
Business logic handler with rental property filtering using LLM + rentals.csv
Includes per-user context memory and operator support for bedrooms/bathrooms.
"""
import os 
import pandas as pd


# Load rentals.csv once when this module is imported
CSV_PATH = os.path.join(os.path.dirname(__file__), "rentals.csv")
try:
    rentals_df = pd.read_csv(CSV_PATH)
except Exception as e:
    rentals_df = pd.DataFrame()
    print(f"Error loading rentals.csv: {e}")

# --- In-memory context (resets when program restarts) ---
user_context = {}  # maps sender -> last used filters


def handle_user_query(sender: str, understood_query: dict) -> str:
    """
    Handles user queries using CSV rental data + LLM analysis.
    Maintains per-user context for progressive filtering.
    """
    original_message = understood_query["original_query"]
    llm_analysis = understood_query["llm_analysis"]

    # If rentals.csv failed to load
    if rentals_df.empty:
        return "Sorry, I couldn't load the rentals database. Please try again later."

    # Handle explicit reset command
    if "reset" in original_message.lower():
        user_context[sender] = {}
        return "Your search filters have been reset."

    # If the LLM returned structured JSON with property intent
    if (
        isinstance(llm_analysis, dict)
        and llm_analysis.get("intent") == "property_search"
    ):
        prev_filters = user_context.get(sender, {})
        new_filters = llm_analysis.get("key_info", {})

        # Merge filters: keep old ones unless new ones overwrite them
        merged_filters = {
            **prev_filters,
            **{k: v for k, v in new_filters.items() if v is not None},
        }

        # Save updated context
        user_context[sender] = merged_filters

        return handle_rental_query(
            original_message, {"key_info": merged_filters}, sender
        )

    # Fallbacks: keyword-based matching if no intent given
    message_lower = original_message.lower()
    if any(word in message_lower for word in ["price", "cost", "how much"]):
        return handle_pricing_query(original_message, llm_analysis)

    elif any(word in message_lower for word in ["book", "schedule", "appointment"]):
        return handle_booking_query(original_message, llm_analysis)

    elif any(
        word in message_lower
        for word in ["problem", "issue", "complaint", "not working"]
    ):
        return handle_support_query(original_message, llm_analysis)

    elif isinstance(llm_analysis, dict) and llm_analysis.get("urgency") == "high":
        return handle_urgent_query(original_message, llm_analysis)

    else:
        return handle_general_query(original_message, llm_analysis)


def apply_operator_filter(df, column, value, operator):
    """Apply filter with operator for numeric columns."""
    if value is None or column not in df.columns:
        return df
    if operator is None:
        operator = ">="
    if operator == ">=":
        return df[df[column] >= value]
    if operator == "<=":
        return df[df[column] <= value]
    if operator == ">":
        return df[df[column] > value]
    if operator == "<":
        return df[df[column] < value]
    if operator == "==":
        return df[df[column] == value]
    return df


def handle_rental_query(original_message: str, llm_analysis: dict, sender: str) -> str:
    """
    Handles rental property queries by filtering rentals.csv step by step.
    Reminds user of current active filters.
    """
    filters = llm_analysis.get("key_info", {}) if isinstance(llm_analysis, dict) else {}

    # Start with full dataset
    df = rentals_df.copy()

    # Normalize numeric columns
    for col in ["price", "bedrooms", "bathrooms"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Apply filters step by step
    if filters.get("budget_min") is not None:
        df = df[df["price"] >= filters["budget_min"]]

    if filters.get("budget_max") is not None:
        df = df[df["price"] <= filters["budget_max"]]

    df = apply_operator_filter(df, "bedrooms", filters.get("bedrooms"), filters.get("bedroom_operator"))
    df = apply_operator_filter(df, "bathrooms", filters.get("bathrooms"), filters.get("bathroom_operator"))

    if filters.get("location"):
        loc = filters["location"]
        conds = []
        for col in ["state", "city", "formattedAddress"]:
            if col in df.columns:
                conds.append(df[col].astype(str).str.contains(loc, case=False, na=False))
        if conds:
            df = df[pd.concat(conds, axis=1).any(axis=1)]

    # If nothing found
    if df.empty:
        return "Sorry, I couldn't find any properties matching your request."

    # Build filter summary to remind user
    filter_summary = []
    if filters.get("location"):
        filter_summary.append(f"Location: {filters['location']}")
    if filters.get("budget_min") is not None:
        filter_summary.append(f"Min budget: ${filters['budget_min']}")
    if filters.get("budget_max") is not None:
        filter_summary.append(f"Max budget: ${filters['budget_max']}")
    if filters.get("bedrooms") is not None:
        filter_summary.append(f"Bedrooms {filters.get('bedroom_operator', '>=')} {filters['bedrooms']}")
    if filters.get("bathrooms") is not None:
        filter_summary.append(f"Bathrooms {filters.get('bathroom_operator', '>=')} {filters['bathrooms']}")

    filter_summary_text = ", ".join(filter_summary) if filter_summary else "No active filters"

    # Format top 5 results
    results = df.head(5).to_dict(orient="records")
    response_lines = [f"Here are some properties that match your request (Active filters: {filter_summary_text}):\n"]
    for r in results:
        address = r.get("formattedAddress") or f"{r.get('city', 'Unknown')}, {r.get('state', '')}"
        agent_name = r.get("agent_name", "Unknown Agent")
        agent_phone = r.get("agent_phone", "No phone")
        agent_email = r.get("agent_email", "No email")

        line = (
            f"- {address} "
            f"| ${r.get('price', 'N/A')} "
            f"| {r.get('bedrooms', '?')} bed / {r.get('bathrooms', '?')} bath "
            f"| Agent: {agent_name}, Phone: {agent_phone}, Email: {agent_email}"
        )
        response_lines.append(line)

    return "\n".join(response_lines)


# --- Existing Handlers ---
def handle_pricing_query(original_message: str, llm_analysis: dict) -> str:
    return "For pricing information, I can connect you with our sales team or you can visit our pricing page. What specific product are you interested in?"


def handle_booking_query(original_message: str, llm_analysis: dict) -> str:
    return "I'd be happy to help you schedule something. Could you let me know what type of appointment you need and your preferred dates?"


def handle_support_query(original_message: str, llm_analysis: dict) -> str:
    return "I'm sorry you're experiencing an issue. Let me help you with that. Can you provide more details about what's happening?"


def handle_urgent_query(original_message: str, llm_analysis: dict) -> str:
    return "I understand this is urgent. Let me escalate this right away and get you the immediate assistance you need."


def handle_general_query(original_message: str, llm_analysis: dict) -> str:
    return "I'm here to help! Could you provide a bit more detail about what you're looking for?"


# Example of a custom function (extendable)
def custom_function_example(data):
    pass
