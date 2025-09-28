import os
from dotenv import load_dotenv
from agentmail import AgentMail

# Load API key from .env
load_dotenv()
api_key = os.getenv("AGENTMAIL_API_KEY")

if not api_key:
    raise ValueError("❌ Missing AGENTMAIL_API_KEY in .env file")

# Initialize AgentMail client
client = AgentMail(api_key=api_key)

# 1. Create an inbox
print("📬 Creating inbox...")
inbox = client.inboxes.create()
print(f"✅ Inbox created: {inbox.address}")

# 2. Create an agent with custom reply behavior
print("🤖 Creating agent...")
agent = client.agents.create(
    name="RealtorResponder",
    instructions="""
    You are an assistant that replies politely to realtors.
    - Always confirm interest in scheduling a viewing.
    - Ask for available times and details about the property.
    - Forward any attachments or key info to raymond@example.com.
    """
)
print(f"✅ Agent created: {agent.name}")

# 3. Attach the agent to the inbox
print("🔗 Attaching agent to inbox...")
client.inboxes.attach_agent(inbox.id, agent.id)
print("✅ Agent attached!")

# 4. Send a test email to a realtor
print("📨 Sending test email...")
client.emails.send(
    inbox_id=inbox.id,
    to="realtor@example.com",  # replace with a real realtor email
    subject="Apartment Viewing Inquiry",
    body="""
    Hi, I’m interested in scheduling a viewing for one of your listings.
    Could you please share available times?
    """
)
print("✅ Test email sent!")