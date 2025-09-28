from datetime import datetime, timezone
from uuid import uuid4
import json
import os
import google.generativeai as genai
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
from dotenv import load_dotenv

load_dotenv()

# Import your custom business logic
from business_logic import handle_user_query

# Configure Gemini client
genai.configure(api_key=os.getenv("API_KEY"))

agent = Agent(
    name = os.getenv("AGENT_NAME"),
    seed = os.getenv("AGENT_SEED"),
    port = 8000,
    mailbox = True
)
chat_proto = Protocol(spec=chat_protocol_spec)


def create_text_chat(text: str) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )


async def understand_query(user_message: str) -> dict:
    """Use Gemini to extract structured info from a query."""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        You are an assistant that extracts structured info from user messages.
        Always respond with ONLY valid JSON.
        Do NOT include explanations, markdown, or code fences.

        The JSON must contain exactly this shape:
        {{
          "intent": one of [
            "property_search", "pricing", "booking", "support", 
            "general", "favorites", "reset", "property_action"
          ],
          "summary": "brief summary of request",
          "key_info": {{
            "budget_min": number or null,
            "budget_max": number or null,
            "bedrooms": number or null,
            "bedroom_operator": one of [">=", "<=", ">", "<", "==", null],
            "bathrooms": number or null,
            "bathroom_operator": one of [">=", "<=", ">", "<", "==", null],
            "city": string or null,
            "state": string or null,
            "location": string or null,
            "property_type": string or null,
            "favorites_action": one of ["show", "add", "remove", null],
            "property_id": string or null,
            "reset": boolean or null,
            "property_action": {{
              "action": one of ["get_contact", "sort", "compare", "details", "show_rent", "send_email", null],
              "property_number": number or null,
              "field": string or null,
              "order": one of ["asc", "desc", null],
              "rental_mode": boolean or null,
              "subject": string or null,
              "body": string or null
            }}
          }},
          "urgency": one of ["low", "medium", "high"]
        }}

        Examples:
        - "give me contact info for property 1" → 
          {{"intent": "property_action", "key_info": {{"property_action": {{"action": "get_contact", "property_number": 1}}}}}}
        - "order the properties by lowest to highest price" → 
          {{"intent": "property_action", "key_info": {{"property_action": {{"action": "sort", "field": "price", "order": "asc"}}}}}}
        - "which has more bedrooms, property 1 or 2" →
          {{"intent": "property_action", "key_info": {{"property_action": {{"action": "compare", "field": "bedrooms"}}}}}}
        - "show me rental properties in Austin" →
          {{"intent": "property_action", "key_info": {{"property_action": {{"action": "show_rent", "rental_mode": true}}}}}}
        - "send an email to the realtor for property 2 saying I'd like to schedule a tour this week" →
          {{"intent": "property_action", "key_info": {{"property_action": {{"action": "send_email", "property_number": 2, "subject": "Property Inquiry", "body": "I'd like to schedule a tour this week"}}}}}}

        User message: {user_message}
        """

        resp = model.generate_content(prompt)
        llm_text = resp.text.strip()

        if llm_text.startswith("```"):
            llm_text = llm_text.strip("`")
            if llm_text.lower().startswith("json"):
                llm_text = llm_text[4:].strip()

        try:
            parsed = json.loads(llm_text)
        except json.JSONDecodeError:
            parsed = {"error": f"Invalid JSON: {llm_text}"}

        return {
            "original_query": user_message,
            "llm_analysis": parsed,
            "timestamp": datetime.now(timezone.utc)
        }

    except Exception as e:
        return {
            "original_query": user_message,
            "llm_analysis": {"error": str(e)},
            "timestamp": datetime.now(timezone.utc)
        }



@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    # Send acknowledgement
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg.msg_id
    ))

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            response = create_text_chat("Hello! How can I help you today?")
            await ctx.send(sender, response)

        elif isinstance(item, TextContent):
            ctx.logger.info(f"Received: {item.text}")

            # 1. LLM understands the query
            understood_query = await understand_query(item.text)
            ctx.logger.info(f"LLM Analysis: {understood_query['llm_analysis']}")

            # 2. Pass to your custom business logic
            business_response = handle_user_query(sender, understood_query)

            # 3. Send response back
            response = create_text_chat(business_response)
            await ctx.send(sender, response)

        elif isinstance(item, EndSessionContent):
            response = create_text_chat("Goodbye!")
            await ctx.send(sender, response)


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Message acknowledged by {sender}")


agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()