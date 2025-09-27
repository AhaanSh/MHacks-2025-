# app.py
import os, json, math
from datetime import datetime
from uuid import uuid4
from typing import Any, Dict, List, Optional

import pandas as pd
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatMessage, ChatAcknowledgement, TextContent,
    StartSessionContent, EndSessionContent, chat_protocol_spec
)

# ---------- Config ----------
CSV_PATH = os.getenv("RENTALS_CSV", "rentals.csv")
ASI1_API_KEY = os.getenv("ASI1_API_KEY")               # required
ASI1_BASE_URL = os.getenv("ASI1_BASE_URL", "https://api.asi1.ai/v1")
ASI1_MODEL = os.getenv("ASI1_MODEL", "asi1-mini")      # fast/general; can use asi1-extended for richer extraction
TOP_K = int(os.getenv("TOP_K", "5"))

# ---------- Data Load ----------
df = pd.read_csv(CSV_PATH)
# normalize columns (strip/standardize)
df.columns = [c.strip().lower() for c in df.columns]
for c in ["price","bedrooms","bathrooms","squarefootage","daysonmarket","hoa_fee","latitude","longitude"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# ---------- Chat Protocol ----------
chat_proto = Protocol(spec=chat_protocol_spec)

def _chat_text(text: str, end_session: bool = False) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content)

# ---------- Structured extraction with ASI1 ----------
# We use OpenAI-compatible client pointed at ASI1
from openai import OpenAI
client = OpenAI(api_key=ASI1_API_KEY, base_url=ASI1_BASE_URL)

# JSON schema the model must return
CRITERIA_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "budget_max": {"type": "number"},
        "city": {"type": "string"},
        "state": {"type": "string"},
        "zipCode": {"type": "string"},
        "propertyType": {"type": "string"},
        "min_bedrooms": {"type": "number"},
        "min_bathrooms": {"type": "number"},
        "min_sqft": {"type": "number"},
        "max_hoa": {"type": "number"},
        "listingType": {"type": "string"},            # e.g., "For Sale" / "For Rent"
        "status": {"type": "string"},                 # e.g., "Active"
        "max_days_on_market": {"type": "number"},
        "must_haves": {"type": "array", "items": {"type": "string"}},
        "nice_to_haves": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["budget_max"]
}

SYSTEM_PROMPT = """You extract structured filters for real-estate search from a user's free-text description.
Return ONLY a compact JSON that matches the provided schema.
Infer reasonable defaults if the user omits fields (e.g., leave null). Currency values should be numbers (no commas or $).
"""

def extract_criteria(user_text: str) -> Dict[str, Any]:
    # Ask ASI1 to produce the JSON. We keep it simple & robust.
    res = client.chat.completions.create(
        model=ASI1_MODEL,
        messages=[
            {"role":"system","content": SYSTEM_PROMPT},
            {"role":"user","content": f"User request: {user_text}\nJSON schema: {json.dumps(CRITERIA_SCHEMA)}\nReturn ONLY JSON."}
        ],
        temperature=0.1,
        max_tokens=600
    )
    txt = res.choices[0].message.content.strip()
    # Best-effort JSON parse
    start = txt.find("{")
    end = txt.rfind("}")
    if start >= 0 and end > start:
        txt = txt[start:end+1]
    try:
        obj = json.loads(txt)
    except Exception:
        obj = {}
    return obj

# ---------- Matching & Scoring ----------
def score_row(row, q):
    score = 0.0
    # hard filters first
    if q.get("budget_max") is not None and row.get("price") and row["price"] > q["budget_max"]:
        return -1e9
    if q.get("min_bedrooms") and (row.get("bedrooms") or 0) < q["min_bedrooms"]:
        return -1e9
    if q.get("min_bathrooms") and (row.get("bathrooms") or 0) < q["min_bathrooms"]:
        return -1e9
    if q.get("min_sqft") and (row.get("squarefootage") or 0) < q["min_sqft"]:
        return -1e9
    if q.get("max_hoa") is not None and not pd.isna(row.get("hoa_fee")) and row["hoa_fee"] > q["max_hoa"]:
        return -1e9
    if q.get("listingType") and row.get("listingtype") and str(row["listingtype"]).lower() != str(q["listingType"]).lower():
        return -1e9
    if q.get("status") and row.get("status") and str(row["status"]).lower() != str(q["status"]).lower():
        return -1e9
    if q.get("propertyType") and row.get("propertytype") and str(row["propertytype"]).lower() != str(q["propertyType"]).lower():
        return -1e9
    if q.get("city") and row.get("city") and str(row["city"]).lower() != str(q["city"]).lower():
        return -1e9
    if q.get("state") and row.get("state") and str(row["state"]).lower() != str(q["state"]).lower():
        return -1e9
    if q.get("zipCode") and row.get("zipcode") and str(row["zipcode"]).strip() != str(q["zipCode"]).strip():
        return -1e9

    # soft preferences
    # 1) price closeness (cheaper than budget is better, but not too low)
    if q.get("budget_max") and row.get("price"):
        gap = q["budget_max"] - row["price"]
        # reward being under budget, with diminishing returns
        score += 1000 * (1 - 1 / (1 + max(gap, 0)/max(q["budget_max"],1)))
    # 2) more beds/baths than minimum
    if q.get("min_bedrooms") and row.get("bedrooms"):
        score += 50 * max(0, row["bedrooms"] - q["min_bedrooms"])
    if q.get("min_bathrooms") and row.get("bathrooms"):
        score += 40 * max(0, row["bathrooms"] - q["min_bathrooms"])
    # 3) larger sqft
    if q.get("min_sqft") and row.get("squarefootage"):
        score += 0.02 * max(0, row["squarefootage"] - q["min_sqft"])
    # 4) fewer days on market
    if row.get("daysonmarket") and not math.isnan(row["daysonmarket"]):
        score += 20 * (1 / (1 + row["daysonmarket"]))
    # 5) lower HOA
    if not pd.isna(row.get("hoa_fee")):
        score += 5 * (1 / (1 + row["hoa_fee"]))

    return score

def recommend(q: Dict[str, Any], top_k: int = TOP_K) -> List[Dict[str, Any]]:
    # iterate rows with dictlike access
    scores = []
    for _, r in df.iterrows():
        s = score_row(r.to_dict(), q)
        if s > -1e8:
            scores.append((s, r))
    scores.sort(key=lambda t: t[0], reverse=True)
    out = []
    for s, r in scores[:top_k]:
        out.append({
            "formattedAddress": r.get("formattedaddress") or r.get("ormattedaddress") or "",
            "city": r.get("city"), "state": r.get("state"), "zipCode": r.get("zipcode"),
            "propertyType": r.get("propertytype"),
            "bedrooms": r.get("bedrooms"), "bathrooms": r.get("bathrooms"),
            "squareFootage": r.get("squarefootage"),
            "status": r.get("status"), "price": r.get("price"),
            "listingType": r.get("listingtype"),
            "daysOnMarket": r.get("daysonmarket"),
            "hoa_fee": r.get("hoa_fee"),
            "agent_name": r.get("agent_name"), "agent_phone": r.get("agent_phone"), "agent_email": r.get("agent_email"),
            "office_name": r.get("office_name"), "office_phone": r.get("office_phone"),
            "score": round(float(s), 2)
        })
    return out

# ---------- Agent ----------
agent = Agent(
    name= "RentalRecommender",
    seed= os.getenv("AGENT_SEED","rental recommender seed"),
    mailbox = os.getenv("MAILBOX_URL"),
    mailbox_key = os.getenv("MAILBOX_KEY"),

)


@chat_proto.on_message(ChatMessage)
async def on_chat(ctx: Context, sender: str, msg: ChatMessage):
    # ack
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))

    user_texts = [c.text for c in msg.content if isinstance(c, TextContent)]
    if not user_texts:
        await ctx.send(sender, _chat_text("Please send your criteria in text."))
        return

    query = user_texts[0]
    try:
        criteria = extract_criteria(query)
        if "budget_max" not in criteria or criteria["budget_max"] in (None, "", 0):
            await ctx.send(sender, _chat_text("Please provide a budget (e.g., 'max $2,000 per month' or '$450k')."))
            return

        results = recommend(criteria, TOP_K)
        if not results:
            await ctx.send(sender, _chat_text("No matches based on your filters. Try relaxing a constraint (e.g., budget or min beds)."))
            return

        lines = ["Top matches:"]
        for i, r in enumerate(results, 1):
            addr = r.get("formattedAddress") or f"{r.get('city','')}, {r.get('state','')}"
            price = f"${int(r['price']):,}" if r.get("price") else "N/A"
            bb = f"{int(r['bedrooms']) if r.get('bedrooms')==r.get('bedrooms') else '?'} bd / {float(r['bathrooms']) if r.get('bathrooms')==r.get('bathrooms') else '?'} ba"
            sqft = f"{int(r['squareFootage']):,} sqft" if r.get("squareFootage")==r.get("squareFootage") else ""
            dom = f" | {int(r['daysOnMarket'])} DOM" if r.get("daysOnMarket")==r.get("daysOnMarket") else ""
            hoa = f" | HOA ${int(r['hoa_fee'])}" if r.get("hoa_fee")==r.get("hoa_fee") else ""
            contact = ""
            if r.get("agent_name") or r.get("agent_phone"):
                contact = f"\n   Agent: {r.get('agent_name') or ''} {r.get('agent_phone') or ''}"
            lines.append(f"{i}) {addr} — {price} — {bb} {sqft}{dom}{hoa}{contact}")
        await ctx.send(sender, _chat_text("\n".join(lines)))
    except Exception as e:
        ctx.logger.error(f"Error: {e}")
        await ctx.send(sender, _chat_text("Sorry—something went wrong parsing your criteria."))

# publish Chat Protocol manifest
agent.include(chat_proto, publish_manifest=True)

# ---------- FastAPI health (for Render + Agentverse checks) ----------
app = FastAPI()

@app.get("/ping")
def ping():
    return {"status":"ok", "agent_address": agent.address}

def run_agent():
    agent.run()

if __name__ == "__main__":
    # Run agent and API together (simple dev runner)
    import threading
    threading.Thread(target=run_agent, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT","8000")))
