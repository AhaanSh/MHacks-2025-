# agents.py
from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
    StartSessionContent,
    EndSessionContent,
)
from functions import CriteriaRequest, RecommendationResponse, get_recommendations
from datetime import datetime
from uuid import uuid4
from typing import Any, Dict

class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: Dict[str, Any]

class StructuredOutputResponse(Model):
    output: Dict[str, Any]

# Address of the LLM-backed AI agent (ASI1 or OpenAI-compatible)
AI_AGENT_ADDRESS = "agent1qtlpfshtlcxekgrfcpmv7m9zpajuwu7d5jfyachvpa4u3dkt6k0uwwp2lct"

##############
agent = Agent(name="RentalAgent", seed="MhacksAhaanShah", port=8001, endpoint=["https://localhost:8001"], mailbox=True)

chat_proto = Protocol(spec=chat_protocol_spec)
struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Got a message from {sender}: {msg.content}")
    ctx.storage.set(str(ctx.session), sender)
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Got a start session message from {sender}")
            continue
        elif isinstance(item, TextContent):
            ctx.logger.info(f"User query: {item.text}")
            ctx.storage.set(str(ctx.session), sender)
            # Ask AI agent to extract structured criteria
            await ctx.send(
                AI_AGENT_ADDRESS,
                StructuredOutputPrompt(
                    prompt=item.text, output_schema=CriteriaRequest.schema()
                ),
            )
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )

@struct_output_client_proto.on_message(StructuredOutputResponse)
async def handle_structured_output_response(
    ctx: Context, sender: str, msg: StructuredOutputResponse
):
    ctx.logger.info(f"Structured output received: {msg.output}")
    session_sender = ctx.storage.get(str(ctx.session))
    if session_sender is None:
        ctx.logger.error("No session sender found in storage")
        return

    # Extract query from structured output
    try:
        query = msg.output.get("query") if isinstance(msg.output, dict) else None
    except Exception:
        query = None
    ctx.logger.info(f"Query extracted: {query}")

    if not query:
        await ctx.send(
            session_sender,
            create_text_chat("Sorry, I couldn't process your request. Please try again."),
        )
        return

    try:
        recs = get_recommendations(query)
    except Exception as err:
        ctx.logger.error(f"Error in recommendation: {err}")
        await ctx.send(
            session_sender,
            create_text_chat("Something went wrong while finding recommendations."),
        )
        return

    results = recs.get("results", [])
    if not results:
        await ctx.send(
            session_sender,
            create_text_chat("No matches found. Try adjusting your criteria."),
        )
        return

    # Format top results
    lines = ["Here are the top matches:"]
    for i, r in enumerate(results, 1):
        addr = r.get("address") or f"{r.get('city','')}, {r.get('state','')}"
        price = f"${int(r['price']):,}" if r.get("price") else "N/A"
        bb = f"{r.get('beds') or '?'} bd / {r.get('baths') or '?'} ba"
        sqft = f"{int(r['sqft']):,} sqft" if r.get("sqft") else ""
        score = f" (score {r.get('score')})"
        lines.append(f"{i}) {addr} — {price} — {bb} {sqft}{score}")

    reply = "\n".join(lines)
    await ctx.send(session_sender, create_text_chat(reply))

agent.include(chat_proto, publish_manifest=True)
agent.include(struct_output_client_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
