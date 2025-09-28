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
- Enhanced Favorites support (per-user add/remove/list with natural language)
- Fixed phone number formatting (removes .0)
- Fixed remove favorites functionality
"""
import os
import re
from typing import Any, Dict, Optional, List

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
user_favorites: Dict[str, List[str]] = {}  # favorites store per user
user_last_search_results: Dict[str, List[Dict[str, Any]]] = {}  # track last search results per user
user_last_favorites_display: Dict[str, List[Dict[str, Any]]] = {}  # track last favorites display

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

def handle_property_action(sender: str, action_info: Dict[str, Any]) -> str:
    # If no search results exist, do a basic search first
    if sender not in user_last_search_results or not user_last_search_results[sender]:
        # Initialize context if needed
        if sender not in user_context:
            user_context[sender] = {}
        
        # Do a basic search to populate results
        basic_search_result = _run_rental_query(sender, {})
        
        # Check if we have results now
        if sender not in user_last_search_results or not user_last_search_results[sender]:
            return "I couldn't find any properties in the database. Please try a specific search query first."

    results = user_last_search_results[sender]

    action = action_info.get("action")
    prop_num = action_info.get("property_number")
    field = action_info.get("field")
    order = action_info.get("order")
    rental_mode = action_info.get("rental_mode", False)

    # Contact info lookup
    if action == "get_contact":
        if not prop_num or prop_num < 1 or prop_num > len(results):
            return f"Property {prop_num} not found."
        row = results[prop_num - 1]
        contact = build_contact_info(row)
        return f"Contact info for property {prop_num}: {contact or 'Not available'}"

    # Sorting
    if action == "sort":
        if not field:
            return "Please specify a field to sort by (e.g., price, bedrooms, bathrooms)."
        df = pd.DataFrame(results)
        if field not in df.columns:
            return f"I can't sort by {field}. Available fields: {list(df.columns)}"
        df_sorted = df.sort_values(by=field, ascending=(order != "desc"))
        return _format_results(df_sorted, {}, sender, prefix=f"Properties sorted by {field} ({order or 'asc'})", rental_mode=rental_mode)

    # Comparison
    if action == "compare":
        if not field:
            return "Please specify what to compare (e.g., price, bedrooms, bathrooms)."
        if len(results) < 2:
            return "You need at least 2 properties in your results to compare."
        row1, row2 = results[0], results[1]
        val1, val2 = row1.get(field), row2.get(field)
        return f"Property 1 has {val1} {field}, Property 2 has {val2} {field}."

    # Details
    if action == "details":
        if not prop_num or prop_num < 1 or prop_num > len(results):
            return f"Property {prop_num} not found."
        row = results[prop_num - 1]
        return format_property_details(row, prop_num, include_rent=rental_mode)
    
    elif action == "send_email":
        prop_num = action_info.get("property_number")
        subject = action_info.get("subject", "Inquiry about property")
        body = action_info.get("body", "Hello, I am interested in this property. Please provide more details.")

        results = user_last_search_results.get(sender, [])
        if not results:
            return "Please run a property search first to get a list of properties."

        if prop_num is None or prop_num < 1 or prop_num > len(results):
            return f"Property {prop_num} not found."

        row = results[prop_num - 1]
        try:
            from realtor import send_email_to_realtor
            return send_email_to_realtor(row, subject, body)
        except ImportError as e:
            # AgentMail not available, return a helpful message
            agent_email = row.get("agent_email", "No email available")
            return f"📧 Email functionality temporarily unavailable. Please contact the agent directly at: {agent_email}"
        except Exception as e:
            return f"⚠️ Failed to send email: {str(e)}"

    # Show rentals
    if action == "show_rent" or rental_mode:
        df = pd.DataFrame(results)
        return _format_results(df, {}, sender, prefix="Rental property estimates", show_favorite_option=True, rental_mode=True)

    return "Sorry, I didn’t understand the property action."

def _normalize_text_for_match(s: str) -> str:
    if s is None:
        return ""
    s = str(s).lower().strip()
    # remove punctuation and extra whitespace
    s = re.sub(r"[-_\/]", " ", s)
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def resolve_property_type(df: pd.DataFrame, requested_type: str) -> Optional[str]:
    """
    Map a user-provided property type string to the best-matching
    propertyType value present in the dataframe.

    Returns the matched propertyType (original case) or None if no match.
    """
    if not requested_type or "propertyType" not in df.columns:
        return None

    req_norm = _normalize_text_for_match(requested_type)

    # Build list of unique types present in the dataset
    unique_types = [t for t in pd.Series(df["propertyType"].dropna().unique()).tolist() if t is not None]

    # Normalized map for quick equality lookup
    norm_map = {}
    for t in unique_types:
        norm = _normalize_text_for_match(t)
        if norm:
            norm_map.setdefault(norm, t)

    # 1) Direct normalized equality
    if req_norm in norm_map:
        return norm_map[req_norm]

    # 2) Substring match against original strings (user -> dataset)
    for t in unique_types:
        if req_norm and req_norm in str(t).lower():
            return t

    # 3) Substring match against normalized dataset strings (dataset -> user)
    for norm, orig in norm_map.items():
        if norm and (norm in req_norm or req_norm in norm):
            return orig

    # 4) Synonyms map (common user words -> canonical tokens)
    SYNONYMS = {
        "apartment": ["apartment", "apartments", "apt", "apts", "flat", "flats"],
        "condo": ["condo", "condominium", "condos", "condominiums"],
        "townhouse": ["townhouse", "townhomes", "townhome", "townhouses"],
        "singlefamily": ["single family", "single-family", "singlefamily", "house", "houses", "home", "homes"],
        "multifamily": ["multi family", "multi-family", "multifamily", "multi unit", "multi-units", "duplex", "triplex", "fourplex", "plex"]
    }

    # If user term clearly matches a synonym set, try to find dataset types that align
    for canon, words in SYNONYMS.items():
        for w in words:
            if w in req_norm or req_norm in _normalize_text_for_match(w):
                # Try to find a dataset entry that contains any of the synonyms or canonical token
                for t in unique_types:
                    tnorm = _normalize_text_for_match(t)
                    if any(_normalize_text_for_match(x) in tnorm for x in (words + [canon])):
                        return t

    # 5) Special heuristics for "apartment": prefer Multi-Family or Condo if present
    # (this covers the common case where dataset uses "Multi-Family" for apartment buildings)
    apt_keywords = {"apartment", "apt", "flat", "apts", "apartments"}
    if any(k in req_norm for k in apt_keywords):
        # prefer Multi-Family if available
        for t in unique_types:
            tnorm = _normalize_text_for_match(t)
            if "multi" in tnorm or "multi family" in tnorm or "multi-family" in tnorm:
                return t
        # then prefer Condo
        for t in unique_types:
            tnorm = _normalize_text_for_match(t)
            if "condo" in tnorm or "condominium" in tnorm:
                return t
        # otherwise return the first dataset type that contains 'apt' / 'apartment'
        for t in unique_types:
            tnorm = _normalize_text_for_match(t)
            if "apt" in tnorm or "apartment" in tnorm:
                return t

    # 6) Token-overlap heuristic (pick dataset type with most shared tokens)
    req_tokens = set([tok for tok in re.split(r"\W+", req_norm) if tok])
    best = None
    best_score = 0
    for t in unique_types:
        tokens = set([tok for tok in re.split(r"\W+", _normalize_text_for_match(t)) if tok])
        score = len(req_tokens & tokens)
        if score > best_score:
            best_score = score
            best = t
    if best_score > 0:
        return best

    # no match found
    return None


def format_property_details(row: Dict[str, Any], prop_num: int, include_rent: bool = False) -> str:
    """Return a nicely formatted details string for one property."""
    lines = [f"Details for property {prop_num}:"]
    
    address = clean_value(row.get("formattedAddress")) or row.get("addressLine1") or "Unknown"
    price_val = row.get("price")
    price = pretty_price(price_val)

    if include_rent and pd.notna(price_val):
        try:
            rent_estimate = round(float(price_val) * 0.01)
            price = f"Rent Estimate: ${rent_estimate:,}/month"
        except Exception:
            pass

    beds = row.get("bedrooms")
    baths = row.get("bathrooms")
    sqft = row.get("squareFootage")
    lot = row.get("lotSize")
    year = row.get("yearBuilt")
    status = row.get("status")
    listing_type = row.get("listingType")
    dom = row.get("daysOnMarket")

    lines.append(f"- Address: {address}")
    if price: 
        lines.append(f"- {price}")
    if pd.notna(beds): 
        lines.append(f"- Bedrooms: {int(beds)}")
    if pd.notna(baths): 
        lines.append(f"- Bathrooms: {int(baths)}")
    if pd.notna(sqft): 
        lines.append(f"- Square Footage: {int(sqft)}")
    if pd.notna(lot): 
        lines.append(f"- Lot Size: {int(lot)}")
    if pd.notna(year): 
        lines.append(f"- Year Built: {int(year)}")
    if status: 
        lines.append(f"- Status: {status}")
    if listing_type: 
        lines.append(f"- Listing Type: {listing_type}")
    if pd.notna(dom): 
        lines.append(f"- Days on Market: {dom}")
    
    contact = build_contact_info(row)
    if contact: 
        lines.append(f"- Contact: {contact}")

    return "\n".join(lines)

def normalize_operator(op: Optional[str]) -> Optional[str]:
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
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    try:
        num = int(float(val))
        return f"${num:,}"
    except Exception:
        return str(val)


def clean_value(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None
    return s


def build_contact_info(row: Dict[str, Any]) -> Optional[str]:
    parts = []
    if row.get("agent_name"):
        parts.append(str(row["agent_name"]).strip())
    if row.get("agent_phone") and str(row["agent_phone"]).lower() != "nan":
        phone = str(row["agent_phone"]).strip()
        # Remove .0 from phone numbers
        if phone.endswith('.0'):
            phone = phone[:-2]
        parts.append(phone)
    if row.get("agent_email") and str(row["agent_email"]).lower() != "nan":
        parts.append(str(row["agent_email"]).strip())

    if parts:
        return ", ".join(parts)

    office_parts = []
    if row.get("office_name"):
        office_parts.append(str(row["office_name"]).strip())
    if row.get("office_phone") and str(row["office_phone"]).lower() != "nan":
        phone = str(row["office_phone"]).strip()
        # Remove .0 from phone numbers
        if phone.endswith('.0'):
            phone = phone[:-2]
        office_parts.append(phone)
    if row.get("office_email") and str(row["office_email"]).lower() != "nan":
        office_parts.append(str(row["office_email"]).strip())

    if office_parts:
        return ", ".join(office_parts)

    return None


def summarize_filters(filters: Dict[str, Any]) -> str:
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
    if not text:
        return False
    t = text.lower()
    phrases = [
        "reset filters", "clear filters", "reset search", "clear search",
        "start over", "clear all filters", "clear all", "reset all filters"
    ]
    for p in phrases:
        if p in t:
            return True
    return False


# ---------------- Enhanced Favorites ----------------
def add_favorite(sender: str, property_id: str) -> str:
    """Add a property to user's favorites"""
    favs = user_favorites.setdefault(sender, [])
    if property_id not in favs:
        favs.append(property_id)
        return f"Property {property_id} added to your favorites."
    return f"Property {property_id} is already in your favorites."


def remove_favorite(sender: str, property_id: str) -> str:
    """Remove a property from user's favorites"""
    favs = user_favorites.get(sender, [])
    if property_id in favs:
        favs.remove(property_id)
        return f"Property {property_id} removed from your favorites."
    return f"Property {property_id} was not in your favorites."


def list_favorites(sender: str) -> str:
    """List all favorite properties for a user"""
    favs = user_favorites.get(sender, [])
    if not favs:
        return "You don't have any favorite properties yet. When you search for properties, you can add them to favorites by saying 'favorite 1', 'favorite 2', etc."

    df = rentals_df.copy()
    
    # Try to find matching properties using the actual favorite IDs
    matched_properties = []
    
    for fav_id in favs:
        # Strategy 1: Match by exact ID (removing quotes)
        if "id" in df.columns:
            df_clean = df.copy()
            df_clean["id_clean"] = df_clean["id"].astype(str).str.strip('"')
            id_matches = df_clean[df_clean["id_clean"] == str(fav_id).strip('"')]
            if not id_matches.empty:
                matched_properties.extend(id_matches.to_dict('records'))
                continue
        
        # Strategy 2: Match by formattedAddress (exact match)
        if "formattedAddress" in df.columns:
            addr_matches = df[df["formattedAddress"].astype(str) == str(fav_id)]
            if not addr_matches.empty:
                matched_properties.extend(addr_matches.to_dict('records'))
                continue
        
        # Strategy 3: Match by normalized address (spaces vs hyphens)
        if "formattedAddress" in df.columns:
            # Try both directions: fav_id might have hyphens, address might have spaces
            normalized_fav = str(fav_id).replace(' ', '-')
            normalized_addresses = df["formattedAddress"].astype(str).str.replace(' ', '-')
            normalized_matches = df[normalized_addresses == normalized_fav]
            if not normalized_matches.empty:
                matched_properties.extend(normalized_matches.to_dict('records'))
                continue
            
            # Also try the reverse: fav_id might have spaces, address might have hyphens
            reverse_fav = str(fav_id).replace('-', ' ')
            reverse_matches = df[df["formattedAddress"].astype(str) == reverse_fav]
            if not reverse_matches.empty:
                matched_properties.extend(reverse_matches.to_dict('records'))
                continue
    
    # Remove duplicates by ID
    unique_properties = []
    seen_ids = set()
    for prop in matched_properties:
        prop_id = prop.get('id') or prop.get('formattedAddress')
        if prop_id and prop_id not in seen_ids:
            seen_ids.add(prop_id)
            unique_properties.append(prop)

    if not unique_properties:
        return f"Your favorites list contains {len(favs)} items but none could be found in the current property data. Your favorites: {favs}"

    # Store the displayed favorites for removal by position
    user_last_favorites_display[sender] = unique_properties
    
    # Create a DataFrame for formatting
    matched_df = pd.DataFrame(unique_properties)
    return _format_results(matched_df, {}, sender, prefix="Here are your favorite properties", show_favorite_option=False)

def handle_add_to_favorites(sender: str, message: str) -> str:
    """Enhanced add to favorites with better property ID extraction"""
    # Look for simple number patterns first (favorite 1, favorite 2, etc.)
    simple_match = re.search(r"favorite\s+(?:property\s+)?(\d+)", message.lower())
    if simple_match:
        property_number = int(simple_match.group(1))
        # Get the actual property from recent search results
        return add_favorite_by_position(sender, property_number)
    
    # Look for other property ID patterns
    id_patterns = [
        r"favorite\s+property\s+([^\s,]+)",  # "favorite property 3"
        r"favorite\s+([^\s,]+)",             # "favorite 12345"
        r"add\s+([^\s,]+)\s+to",             # "add 12345 to favorites"
        r"property\s+([^\s,]+)",             # "property 12345" 
        r"id\s*:?\s*([^\s,]+)",              # "id: 12345" or "id 12345"
        r"#([^\s,]+)",                       # "#12345"
        r"\[([^\]]+)\]",                     # "[12345]" - matches our bracket format
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, message.lower())
        if match:
            property_id = match.group(1).strip()
            return add_favorite(sender, property_id)
    
    return "Please specify which property you'd like to add to favorites. You can say 'favorite 1', 'favorite 2', etc. using the property number from your search results."


def add_favorite_by_position(sender: str, position: int) -> str:
    """Add favorite by position number from last search results"""
    if sender not in user_last_search_results:
        return "Please do a property search first to see available options."
    
    results = user_last_search_results[sender]
    
    if position < 1 or position > len(results):
        return f"Property {position} not found. Please choose a number between 1 and {len(results)}."
    
    try:
        property_row = results[position - 1]  # Convert to 0-based index
        property_id = property_row.get("id")
        if property_id is None or pd.isna(property_id):
            # Use address as fallback ID
            address = property_row.get("formattedAddress") or property_row.get("addressLine1") or f"property_{position}"
            property_id = address
        else:
            property_id = str(property_id).strip('"')
        
        return add_favorite(sender, property_id)
    except IndexError:
        return f"Property {position} not found."


def handle_remove_from_favorites(sender: str, message: str) -> str:
    """Enhanced remove from favorites with better property ID extraction"""
    # Look for simple number patterns first (remove favorite 1, unfavorite 2, etc.)
    simple_match = re.search(r"(?:remove\s+favorite|unfavorite|delete\s+favorite)\s+(\d+)", message.lower())
    if simple_match:
        property_number = int(simple_match.group(1))
        # Get the actual property from recent favorites display or search results
        return remove_favorite_by_position(sender, property_number)
    
    # Look for other property ID patterns
    id_patterns = [
        r"remove\s+favorite\s+([^\s,]+)",    # "remove favorite 12345"
        r"unfavorite\s+([^\s,]+)",           # "unfavorite 12345"
        r"delete\s+([^\s,]+)",               # "delete 12345"
        r"property\s+([^\s,]+)",             # "property 12345"
        r"id\s*:?\s*([^\s,]+)",              # "id: 12345"
        r"#([^\s,]+)",                       # "#12345"
        r"\[([^\]]+)\]",                     # "[12345]"
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, message.lower())
        if match:
            property_id = match.group(1)
            return remove_favorite(sender, property_id)
    
    return "Please specify which property you'd like to remove from favorites. You can say 'remove favorite 1', 'unfavorite 2', etc. using the property number from your favorites list."


def remove_favorite_by_position(sender: str, position: int) -> str:
    """Remove favorite by position number from last favorites display or search results"""
    print(f"DEBUG: remove_favorite_by_position called for sender={sender}, position={position}")
    
    # First try to remove from favorites display (if user just viewed favorites)
    if sender in user_last_favorites_display:
        favorites_results = user_last_favorites_display[sender]
        print(f"DEBUG: Found {len(favorites_results)} favorites in display")
        if 1 <= position <= len(favorites_results):
            property_row = favorites_results[position - 1]
            property_id = property_row.get("id") or property_row.get("formattedAddress")
            print(f"DEBUG: Removing property at position {position}: {property_id}")
            
            if property_id is None or pd.isna(property_id):
                # Use address as fallback ID
                address = property_row.get("formattedAddress") or property_row.get("addressLine1") or f"property_{position}"
                property_id = address
            
            property_id = str(property_id).strip('"')
            print(f"DEBUG: Final property ID to remove: {property_id}")
            
            # Get current favorites for debugging
            current_favs = user_favorites.get(sender, [])
            print(f"DEBUG: Current favorites before removal: {current_favs}")
            
            result = remove_favorite(sender, property_id)
            print(f"DEBUG: Removal result: {result}")
            return result
    
    # Fallback to search results
    if sender in user_last_search_results:
        search_results = user_last_search_results[sender]
        print(f"DEBUG: Falling back to search results, found {len(search_results)} properties")
        if 1 <= position <= len(search_results):
            property_row = search_results[position - 1]
            property_id = property_row.get("id") or property_row.get("formattedAddress")
            print(f"DEBUG: Removing search result at position {position}: {property_id}")
            
            if property_id is None or pd.isna(property_id):
                address = property_row.get("formattedAddress") or property_row.get("addressLine1") or f"property_{position}"
                property_id = address
            
            property_id = str(property_id).strip('"')
            print(f"DEBUG: Final property ID to remove: {property_id}")
            
            result = remove_favorite(sender, property_id)
            print(f"DEBUG: Removal result: {result}")
            return result
    
    return f"Property {position} not found. Please view your favorites first or do a property search."

# ---------------- Main handler ----------------
# ---------------- Main handler ----------------
def handle_user_query(sender: str, understood_query: Dict[str, Any]) -> str:
    original_message = understood_query.get("original_query", "") or ""
    llm_analysis = understood_query.get("llm_analysis", {}) or {}

    # init context/favorites
    if sender not in user_context:
        user_context[sender] = {}
    if sender not in user_favorites:
        user_favorites[sender] = []

    lower_msg = original_message.lower()

    # --- FIXED ORDER ---

    # Remove from favorites - must check BEFORE add
    if any(phrase in lower_msg for phrase in [
        "remove from favorites", "unfavorite", "delete from favorites",
        "remove this favorite", "take off favorites", "remove favorite"
    ]):
        return handle_remove_from_favorites(sender, original_message)

    # Add to favorites
    if any(phrase in lower_msg for phrase in [
        "add to favorites", "favorite this", "save this property", 
        "add this to my favorites", "make this a favorite", "favorite "
    ]):
        return handle_add_to_favorites(sender, original_message)

    # Show favorites
    if any(phrase in lower_msg for phrase in [
        "show favorites", "show my favorites", "list favorites", 
        "my favorite properties", "what are my favorites", "favorites list",
        "view favorites", "see my favorites"
    ]):
        return list_favorites(sender)

    # Handle contact info requests directly
    if any(phrase in lower_msg for phrase in [
        "contact info for property", "contact information for property", "give me contact",
        "contact details for property", "phone number for property", "email for property",
        "landlord contact for property", "agent contact for property"
    ]):
        # Extract property number
        import re
        match = re.search(r'property\s+(\d+)', lower_msg)
        if match:
            prop_num = int(match.group(1))
            action_info = {"action": "get_contact", "property_number": prop_num}
            return handle_property_action(sender, action_info)
        else:
            return "Please specify which property number you want contact info for. For example: 'give me contact info for property 1'"

    # Handle email requests directly
    if any(phrase in lower_msg for phrase in [
        "send an email", "email the", "send email", "email about property", "send message",
        "email interest", "email of interest", "contact the landlord", "contact the agent",
        "reach out about property", "inquire about property", "express interest"
    ]):
        # Extract property number
        import re
        match = re.search(r'property\s+(\d+)', lower_msg)
        if match:
            prop_num = int(match.group(1))
            
            # Extract custom message if provided
            custom_message = None
            if "saying" in lower_msg:
                saying_part = lower_msg.split("saying", 1)[1].strip()
                if saying_part:
                    custom_message = saying_part
            elif "about" in lower_msg and "property" not in lower_msg.split("about", 1)[1][:20]:
                about_part = lower_msg.split("about", 1)[1].strip()
                if about_part and "property" not in about_part[:20]:
                    custom_message = about_part
            
            action_info = {
                "action": "send_email", 
                "property_number": prop_num,
                "subject": "Property Inquiry - Interest Expression",
                "body": custom_message or "Hello, I am interested in this property. Could you please provide more details and let me know about availability? I would also like to schedule a viewing if possible. Thank you!"
            }
            return handle_property_action(sender, action_info)
        else:
            return "Please specify which property number you want to email about. For example: 'send an email of interest to property 1'"

    # Handle LLM-detected favorites intent
    if isinstance(llm_analysis, dict) and llm_analysis.get("intent") == "favorites":
        key_info = llm_analysis.get("key_info", {}) or {}
        favorites_action = key_info.get("favorites_action")
        property_id = key_info.get("property_id")

        if favorites_action == "show":
            return list_favorites(sender)
        elif favorites_action == "add":
            if property_id:
                if str(property_id).isdigit():
                    return add_favorite_by_position(sender, int(property_id))
                else:
                    return add_favorite(sender, property_id)
            else:
                return handle_add_to_favorites(sender, original_message)
        elif favorites_action == "remove":
            if property_id:
                if str(property_id).isdigit():
                    return remove_favorite_by_position(sender, int(property_id))
                else:
                    return remove_favorite(sender, property_id)
            else:
                return handle_remove_from_favorites(sender, original_message)
        else:
            return list_favorites(sender)

    # Reset detection
    if _is_reset_command_text(original_message):
        user_context[sender] = {}
        return "Your search filters have been reset."

    if isinstance(llm_analysis, dict):
        if llm_analysis.get("intent") == "reset":
            user_context[sender] = {}
            return "Your search filters have been reset."
        k = llm_analysis.get("key_info", {})
        if isinstance(k, dict) and k.get("reset") in (True, "true", "yes", 1):
            user_context[sender] = {}
            return "Your search filters have been reset."

    # Property search
    if isinstance(llm_analysis, dict) and llm_analysis.get("intent") == "property_search":
        prev = user_context.get(sender, {}) or {}
        incoming = llm_analysis.get("key_info", {}) or {}

        parsed_incoming: Dict[str, Any] = {}
        if "budget_min" in incoming:
            parsed_incoming["budget_min"] = parse_number(incoming.get("budget_min"))
        if "budget_max" in incoming:
            parsed_incoming["budget_max"] = parse_number(incoming.get("budget_max"))
        if "bedrooms" in incoming:
            parsed_incoming["bedrooms"] = parse_number(incoming.get("bedrooms"))
        if "bathrooms" in incoming:
            parsed_incoming["bathrooms"] = parse_number(incoming.get("bathrooms"))
        if "bedroom_operator" in incoming:
            parsed_incoming["bedroom_operator"] = normalize_operator(incoming.get("bedroom_operator"))
        if "bathroom_operator" in incoming:
            parsed_incoming["bathroom_operator"] = normalize_operator(incoming.get("bathroom_operator"))
        if "city" in incoming and incoming.get("city"):
            parsed_incoming["city"] = incoming.get("city")
        if "state" in incoming and incoming.get("state"):
            st = str(incoming.get("state")).strip()
            st_abbr = STATE_MAP.get(st.lower(), None)
            parsed_incoming["state"] = st_abbr or st.upper()
        if "location" in incoming and incoming.get("location"):
            parsed_incoming["location"] = incoming.get("location")
        if "property_type" in incoming and incoming.get("property_type"):
            parsed_incoming["property_type"] = incoming.get("property_type")

        merged = prev.copy()
        for k, v in parsed_incoming.items():
            if v is not None:
                merged[k] = v

        user_context[sender] = merged
        return _run_rental_query(sender, merged)

    # Property actions (sorting, contact info, etc.)
    if isinstance(llm_analysis, dict) and llm_analysis.get("intent") == "property_action":
        key_info = llm_analysis.get("key_info", {}) or {}
        action_info = key_info.get("property_action", {}) or {}
        return handle_property_action(sender, action_info)

    # Other handlers
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

# ---------------- Rentals filtering ----------------
def _run_rental_query(sender: str, filters: Dict[str, Any]) -> str:
    df = rentals_df.copy()

    for c in ["price", "bedrooms", "bathrooms"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if filters.get("budget_min") is not None or filters.get("budget_max") is not None:
        if "price" in df.columns:
            df = df.dropna(subset=["price"])
    if filters.get("bedrooms") is not None and "bedrooms" in df.columns:
        df = df.dropna(subset=["bedrooms"])
    if filters.get("bathrooms") is not None and "bathrooms" in df.columns:
        df = df.dropna(subset=["bathrooms"])

    if filters.get("budget_min") is not None:
        df = df[df["price"] >= float(filters["budget_min"])]
    if filters.get("budget_max") is not None:
        df = df[df["price"] <= float(filters["budget_max"])]

    df = apply_operator_filter(df, "bedrooms", filters.get("bedrooms"), filters.get("bedroom_operator"))
    df = apply_operator_filter(df, "bathrooms", filters.get("bathrooms"), filters.get("bathroom_operator"))

    if filters.get("property_type") and "propertyType" in df.columns:
        requested = str(filters.get("property_type", "")).strip()
        resolved = resolve_property_type(df, requested)
        # debug print (optional) - remove or comment out in production:
        # print(f"DEBUG: requested property_type='{requested}' resolved_to='{resolved}'")
        if resolved:
            # match rows where the dataset propertyType contains the resolved value (case-insensitive)
            df = df[df["propertyType"].astype(str).str.contains(str(resolved), case=False, na=False)]
        else:
            # fallback: try the original user-provided string (loose match)
            df = df[df["propertyType"].astype(str).str.contains(requested, case=False, na=False)]



    if filters.get("city") and "city" in df.columns:
        df = df[df["city"].astype(str).str.contains(str(filters["city"]), case=False, na=False)]

    if filters.get("state") and "state" in df.columns:
        desired_state = str(filters["state"]).upper()
        df = df[df["state"].astype(str).str.upper() == desired_state]

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

    if df.empty:
        return "Sorry, I couldn't find any properties matching your request. (Active filters: " + summarize_filters(filters) + ")"

    if "id" in df.columns:
        df = df.drop_duplicates(subset=["id"])
    elif "formattedAddress" in df.columns:
        df = df.drop_duplicates(subset=["formattedAddress"])

    if "price" in df.columns:
        df = df.sort_values(by="price", ascending=True)

    return _format_results(df, filters, sender)


def _format_results(df: pd.DataFrame, filters: Dict[str, Any], sender: str, prefix: str = "Here are some properties that match your request", show_favorite_option: bool = True, rental_mode: bool = False) -> str:
    results = df.head(5).to_dict(orient="records")
    user_last_search_results[sender] = results.copy()

    if show_favorite_option:
        lines = [f"{prefix} (Active filters: {summarize_filters(filters)}):\n"]
    else:
        lines = [f"{prefix}:\n"]

    for i, row in enumerate(results, 1):
        address = clean_value(row.get("formattedAddress")) or row.get("addressLine1") or row.get("city") or "Unknown"
        price_val = row.get("price")

        if rental_mode and pd.notna(price_val):
            price_str = f"Rent Estimate: ${round(float(price_val) * 0.01):,}/month"
        else:
            price_str = pretty_price(price_val)

        bedrooms_val = row.get("bedrooms")
        bathrooms_val = row.get("bathrooms")
        
        parts = [f"- Property {i}: {address}"]
        if price_str:
            parts.append(price_str)

        br_parts = []
        if pd.notna(bedrooms_val):
            br_parts.append(f"{int(bedrooms_val)} bed")
        if pd.notna(bathrooms_val):
            br_parts.append(f"{int(bathrooms_val)} bath")
        if br_parts:
            parts.append("| " + " / ".join(br_parts))

        contact = build_contact_info(row)
        if contact:
            parts.append("| Contact: " + contact)

        if show_favorite_option:
            parts.append(f"| Say 'favorite {i}' to save")

        lines.append(" ".join(parts))

    if show_favorite_option:
        lines.append("\nTip: Use 'favorite 1', 'favorite 2', etc. to add properties to favorites, then 'show favorites' to view them later")

    return "\n".join(lines)



# --- Other simple handlers ---
def handle_pricing_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "For pricing information, I can connect you with our sales team or you can visit our pricing page."


def handle_booking_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "I'd be happy to help you schedule something. Could you let me know what type of appointment you need and your preferred dates?"


def handle_support_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "I'm sorry you're experiencing an issue. Can you provide more details about what's happening?"


def handle_urgent_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    return "I understand this is urgent. Let me escalate this right away and get you immediate assistance."


def handle_general_query(original_message: str, llm_analysis: Dict[str, Any]) -> str:
    # Check if user is asking for contact info
    lower_msg = original_message.lower()
    if any(term in lower_msg for term in ["contact", "phone", "email", "landlord", "agent", "owner"]):
        return "To get contact information, please first search for properties and then ask for 'contact info for property 1' (or the specific property number). For example: 'show me apartments' then 'give me contact info for property 1'."
    
    return "I'm here to help! Could you provide a bit more detail about what you're looking for? You can search for properties, view your favorites, or ask me anything else."


def custom_function_example(data: Any):
    pass