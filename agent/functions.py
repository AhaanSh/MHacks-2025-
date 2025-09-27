# functions.py
from uagents import Model
import pandas as pd
import math

# ---------- Config ----------
CSV_PATH = "rentals.csv"   # default CSV file path
TOP_K = 5                  # number of top matches to return

# ---------- Data Load ----------
df = pd.read_csv(CSV_PATH)
df.columns = [c.strip().lower() for c in df.columns]

# Ensure numeric types where needed
for c in ["price","bedrooms","bathrooms","squarefootage","daysonmarket","hoa_fee","latitude","longitude"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# ---------- Request / Response Models ----------
class CriteriaRequest(Model):
    budget_max: float
    min_bedrooms: int = 0
    min_bathrooms: int = 0
    min_sqft: int = 0
    max_hoa: float = None
    city: str = None
    state: str = None
    zipCode: str = None

class RecommendationResponse(Model):
    results: list

# ---------- Scoring ----------
def score_row(row, q: CriteriaRequest):
    score = 0.0
    if q.budget_max and row.get("price") and row["price"] > q.budget_max:
        return -1e9
    if q.min_bedrooms and (row.get("bedrooms") or 0) < q.min_bedrooms:
        return -1e9
    if q.min_bathrooms and (row.get("bathrooms") or 0) < q.min_bathrooms:
        return -1e9
    if q.min_sqft and (row.get("squarefootage") or 0) < q.min_sqft:
        return -1e9
    if q.max_hoa is not None and row.get("hoa_fee") and row["hoa_fee"] > q.max_hoa:
        return -1e9

    # soft preferences
    if q.budget_max and row.get("price"):
        gap = q.budget_max - row["price"]
        score += 1000 * (1 - 1/(1+max(gap,0)/max(q.budget_max,1)))
    if q.min_bedrooms and row.get("bedrooms"):
        score += 50 * max(0, row["bedrooms"] - q.min_bedrooms)
    if q.min_bathrooms and row.get("bathrooms"):
        score += 40 * max(0, row["bathrooms"] - q.min_bathrooms)
    if q.min_sqft and row.get("squarefootage"):
        score += 0.02 * max(0, row["squarefootage"] - q.min_sqft)
    if row.get("daysonmarket") and not math.isnan(row["daysonmarket"]):
        score += 20 * (1/(1+row["daysonmarket"]))
    if row.get("hoa_fee") and not math.isnan(row["hoa_fee"]):
        score += 5 * (1/(1+row["hoa_fee"]))
    return score

# ---------- Main Entry ----------
def get_recommendations(criteria: CriteriaRequest):
    """Return rental recommendations based on structured criteria."""
    scored = []
    for _, r in df.iterrows():
        s = score_row(r.to_dict(), criteria)
        if s > -1e8:
            scored.append((s, r))
    scored.sort(key=lambda x: x[0], reverse=True)

    results = [
        {
            "address": r.get("formattedaddress"),
            "price": r.get("price"),
            "beds": r.get("bedrooms"),
            "baths": r.get("bathrooms"),
            "sqft": r.get("squarefootage"),
            "city": r.get("city"),
            "state": r.get("state"),
            "zip": r.get("zipcode"),
            "score": round(float(s), 2),
        }
        for s, r in scored[:TOP_K]
    ]
    return {"results": results}
