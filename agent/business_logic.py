"""
Business logic handler with rental property filtering using LLM + rentals.csv
"""
import pandas as pd
import os

# Load rentals.csv once when this module is imported
CSV_PATH = os.path.join(os.path.dirname(__file__), "rentals.csv")
try:
    rentals_df = pd.read_csv(CSV_PATH)
except Exception as e:
    rentals_df = pd.DataFrame()
    print(f"Error loading rentals.csv: {e}")


def handle_user_query(sender: str, understood_query: dict) -> str:
    """
    Handles user queries using CSV rental data + LLM analysis.
    """
    original_message = understood_query["original_query"]
    llm_analysis = understood_query["llm_analysis"]

    # If rentals.csv failed to load
    if rentals_df.empty:
        return "Sorry, I couldn't load the rentals database. Please try again later."

    # If the LLM returned structured JSON with property intent
    if isinstance(llm_analysis, dict) and llm_analysis.get("intent") == "property_search":
        return handle_rental_query(original_message, llm_analysis)

    # Fallbacks: keyword-based matching if no intent given
    message_lower = original_message.lower()
    if any(word in message_lower for word in ["price", "cost", "how much"]):
        return handle_pricing_query(original_message, llm_analysis)

    elif any(word in message_lower for word in ["book", "schedule", "appointment"]):
        return handle_booking_query(original_message, llm_analysis)

    elif any(word in message_lower for word in ["problem", "issue", "complaint", "not working"]):
        return handle_support_query(original_message, llm_analysis)

    elif isinstance(llm_analysis, dict) and llm_analysis.get("urgency") == "high":
        return handle_urgent_query(original_message, llm_analysis)

    else:
        return handle_general_query(original_message, llm_analysis)


def handle_rental_query(original_message: str, llm_analysis: dict) -> str:
    """
    Handles rental property queries by filtering rentals.csv step by step
    """
    filters = {}
    key_info = llm_analysis.get("key_info", {}) if isinstance(llm_analysis, dict) else {}

    # Extract filters
    if key_info.get("budget_min") is not None:
        filters["budget_min"] = key_info["budget_min"]
    if key_info.get("budget_max") is not None:
        filters["budget_max"] = key_info["budget_max"]

    if key_info.get("bedrooms") is not None:
        filters["bedrooms"] = key_info["bedrooms"]
    if key_info.get("bathrooms") is not None:
        filters["bathrooms"] = key_info["bathrooms"]

    if key_info.get("location"):
        filters["location"] = key_info["location"]

    # Start with full dataset
    df = rentals_df.copy()

    # Normalize numeric columns
    for col in ["price", "bedrooms", "bathrooms"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Apply filters step by step
    if "budget_min" in filters and "price" in df.columns:
        df = df[df["price"] >= filters["budget_min"]]

    if "budget_max" in filters and "price" in df.columns:
        df = df[df["price"] <= filters["budget_max"]]

    if "bedrooms" in filters and "bedrooms" in df.columns:
        df = df[df["bedrooms"] >= filters["bedrooms"]]

    if "bathrooms" in filters and "bathrooms" in df.columns:
        df = df[df["bathrooms"] >= filters["bathrooms"]]

    if "location" in filters:
        loc = filters["location"]
        conds = []
        for col in ["state", "city", "formattedAddress"]:
            if col in df.columns:
                conds.append(df[col].astype(str).str.contains(loc, case=False, na=False))
        if conds:
            df = df[pd.concat(conds, axis=1).any(axis=1)]

    # If nothing found
    if df.empty:
        return "Sorry, I couldn’t find any properties matching your request."

    # Format top 5 results
    results = df.head(5).to_dict(orient="records")
    response_lines = ["Here are some properties that match your request:\n"]
    for r in results:
        address = r.get("formattedAddress") or f"{r.get('city', 'Unknown')}, {r.get('state', '')}"
        line = (
            f"- {address} "
            f"| ${r.get('price', 'N/A')} "
            f"| {r.get('bedrooms', '?')} bed / {r.get('bathrooms', '?')} bath"
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
