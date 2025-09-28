# realtor.py
import os
from dotenv import load_dotenv
from agentmail import AgentMail

# Load API key
load_dotenv()
api_key = os.getenv("AGENTMAIL_API_KEY")

if not api_key:
    raise ValueError("❌ AGENTMAIL_API_KEY not found in .env")

# Initialize client
client = AgentMail(api_key=api_key)

# 1️⃣ Create inbox
print("📬 Creating inbox...")
inbox = client.inboxes.create()
print("✅ Inbox created!")
print("Inbox details:", inbox)

# 2️⃣ List all threads (no inbox_id argument)
print("\n🧵 Listing all threads for this account...")
threads = client.threads.list()  # list all threads
if not threads:
    print("No threads found yet.")
else:
    # Optionally filter threads by inbox_id
    inbox_threads = [t for t in threads if getattr(t, "inbox_id", None) == inbox.inbox_id]
    if not inbox_threads:
        print(f"No threads found in inbox {inbox.inbox_id}.")
    else:
        for t in inbox_threads:
            print(f"Thread ID: {t.thread_id}, Subject: {getattr(t, 'subject', 'N/A')}, Updated at: {t.updated_at}")

# 3️⃣ Read messages in each thread
print("\n✉️ Reading messages in each thread...")
for t in inbox_threads:
    messages = client.threads.get_messages(thread_id=t.thread_id)
    print(f"\nMessages in Thread {t.thread_id}:")
    for m in messages:
        print(f"- From: {getattr(m, 'from_email', 'N/A')}, Subject: {getattr(m, 'subject', 'N/A')}, Body: {getattr(m, 'body', 'N/A')[:100]}...")
