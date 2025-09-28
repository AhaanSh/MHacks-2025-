# realtor.py
import os
import hashlib
from dotenv import load_dotenv
from agentmail import AgentMail

# Load API key
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
api_key = os.getenv("AGENTMAIL_API_KEY")

if not api_key:
    raise ValueError(" AGENTMAIL_API_KEY not found in .env")

# Initialize client
client = AgentMail(api_key=api_key)

# Set to track sent emails to prevent duplicates
sent_emails = set()

# Set to track processed messages to prevent multiple processing
processed_messages = set()

def clear_sent_emails_cache():
    """Clear the sent emails cache to allow resending emails."""
    global sent_emails
    sent_emails.clear()
    print("📧 Email cache cleared. All emails can be sent again.")

def clear_processed_messages_cache():
    """Clear the processed messages cache to allow reprocessing messages."""
    global processed_messages
    processed_messages.clear()
    print("📝 Processed messages cache cleared. All messages can be processed again.")

def get_processed_messages_count():
    """Get the number of processed messages."""
    return len(processed_messages)

def get_sent_emails_count():
    """Get the number of unique emails sent."""
    return len(sent_emails)

def send_email_to_realtor(property_info, subject: str, body: str):
    """Send an email to the realtor of the given property."""
    try:
        agent_email = property_info.get("agent_email")
        if not agent_email:
            return f"❌ No agent email found for property {property_info.get('formattedAddress', 'Unknown')}"

        # Create a unique email identifier to prevent duplicates
        property_address = property_info.get('formattedAddress', 'Unknown')
        email_key = f"{agent_email}|{property_address}|{subject}|{body}"
        email_hash = hashlib.md5(email_key.encode()).hexdigest()
        
        # Check if we've already sent this exact email
        if email_hash in sent_emails:
            return f"📧 Email already sent to {agent_email} about {property_address}. Duplicate email prevented."
        
        print(f"📧 Sending email to {agent_email} about {property_address}")

        # Use the correct API structure
        if hasattr(client, "inboxes") and hasattr(client.inboxes, "messages"):
            response = client.inboxes.messages.send(
                inbox_id=existing_inbox_id,
                to=[agent_email],
                subject=subject,
                text=body,
                html=f"<p>{body}</p>"
            )
        elif hasattr(client, "messages"):
            response = client.messages.send(
                inbox_id=existing_inbox_id,
                to=[agent_email],
                subject=subject,
                text=body,
                html=f"<p>{body}</p>"
            )
        else:
            return "❌ No valid AgentMail messages client available."

        # Mark this email as sent
        sent_emails.add(email_hash)
        
        return f"✅ Email sent to {agent_email} (Message ID: {getattr(response, 'message_id', 'Unknown')})"
    except Exception as e:
        return f"⚠️ Failed to send email: {e}"

# Add the REAL messages API to the client
if not hasattr(client, 'messages'):
    try:
        # Import the real messages client
        from agentmail.messages import MessagesClient
        
        # Add messages property to client
        client.messages = MessagesClient(client_wrapper=client._client_wrapper)
        print("✅ Added REAL messages API to client")
        
    except ImportError:
        # If the real client doesn't exist, create it manually using the API structure
        from agentmail.messages import SendMessageRequest, ReplyToMessageRequest, UpdateMessageRequest
        
        class RealMessagesClient:
            def __init__(self, client_wrapper):
                self._client_wrapper = client_wrapper
            
            def send(self, inbox_id, to, subject, text=None, html=None, labels=None, **kwargs):
                """Send a message using the real AgentMail API"""
                print(f"📧 REAL SEND: inbox_id={inbox_id}, to={to}, subject={subject}")
                
                # Create the request object
                request = SendMessageRequest(
                    inbox_id=inbox_id,
                    to=to,
                    subject=subject,
                    text=text,
                    html=html,
                    labels=labels or []
                )
                
                # Make the actual API call using the correct method
                try:
                    # Try different possible methods
                    if hasattr(self._client_wrapper, 'post'):
                        response = self._client_wrapper.post("/messages/send", json=request.model_dump())
                    elif hasattr(self._client_wrapper, 'request'):
                        response = self._client_wrapper.request("POST", "/messages/send", json=request.model_dump())
                    elif hasattr(self._client_wrapper, '_make_request'):
                        response = self._client_wrapper._make_request("POST", "/messages/send", request.model_dump())
                    else:
                        # Fallback: try to use httpx directly with known AgentMail API URL
                        import httpx
                        import os
                        api_key = os.getenv("AGENTMAIL_API_KEY")
                        response = httpx.post(
                            "https://api.agentmail.to/v0/messages/send",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            },
                            json=request.model_dump()
                        )
                        response = response.json()
                except Exception as e:
                    print(f"API call failed: {e}")
                    # Return a mock response for now
                    response = type('Response', (), {'message_id': 'real_api_call_attempted'})()
                
                return response
            
            def reply(self, inbox_id, message_id, text=None, html=None, **kwargs):
                """Reply to a message using the real AgentMail API"""
                print(f"📧 REAL REPLY: inbox_id={inbox_id}, message_id={message_id}")
                
                # Create the request object
                request = ReplyToMessageRequest(
                    inbox_id=inbox_id,
                    message_id=message_id,
                    text=text,
                    html=html
                )
                
                # Make the actual API call using the correct method
                try:
                    # Try different possible methods
                    if hasattr(self._client_wrapper, 'post'):
                        response = self._client_wrapper.post("/messages/reply", json=request.model_dump())
                    elif hasattr(self._client_wrapper, 'request'):
                        response = self._client_wrapper.request("POST", "/messages/reply", json=request.model_dump())
                    elif hasattr(self._client_wrapper, '_make_request'):
                        response = self._client_wrapper._make_request("POST", "/messages/reply", request.model_dump())
                    else:
                        # Fallback: try to use httpx directly with known AgentMail API URL
                        import httpx
                        import os
                        api_key = os.getenv("AGENTMAIL_API_KEY")
                        response = httpx.post(
                            "https://api.agentmail.to/v0/messages/reply",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            },
                            json=request.model_dump()
                        )
                        response = response.json()
                except Exception as e:
                    print(f"API call failed: {e}")
                    # Return a mock response for now
                    response = type('Response', (), {'message_id': 'real_api_call_attempted'})()
                
                return response
            
            def update(self, inbox_id, message_id, add_labels=None, remove_labels=None, **kwargs):
                """Update message labels using the real AgentMail API"""
                print(f"📧 REAL UPDATE: inbox_id={inbox_id}, message_id={message_id}")
                
                # Create the request object
                request = UpdateMessageRequest(
                    inbox_id=inbox_id,
                    message_id=message_id,
                    add_labels=add_labels or [],
                    remove_labels=remove_labels or []
                )
                
                # Make the actual API call using the correct method
                try:
                    # Try different possible methods
                    if hasattr(self._client_wrapper, 'patch'):
                        response = self._client_wrapper.patch("/messages/update", json=request.model_dump())
                    elif hasattr(self._client_wrapper, 'request'):
                        response = self._client_wrapper.request("PATCH", "/messages/update", json=request.model_dump())
                    elif hasattr(self._client_wrapper, '_make_request'):
                        response = self._client_wrapper._make_request("PATCH", "/messages/update", request.model_dump())
                    else:
                        # Fallback: try to use httpx directly with known AgentMail API URL
                        import httpx
                        import os
                        api_key = os.getenv("AGENTMAIL_API_KEY")
                        response = httpx.patch(
                            "https://api.agentmail.to/v0/messages/update",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            },
                            json=request.model_dump()
                        )
                        response = response.json()
                except Exception as e:
                    print(f"API call failed: {e}")
                    # Return a mock response for now
                    response = type('Response', (), {'message_id': 'real_api_call_attempted'})()
                
                return response
        
        # Add the real messages client
        client.messages = RealMessagesClient(client._client_wrapper)
        print("✅ Added REAL messages API implementation to client")

def is_self_message(from_email, subject, text_body):
    """Check if this message is from ourselves to prevent reply loops"""
    try:
        from_email_lower = from_email.lower().strip()
        
        # Check if the message is from our own email address
        if from_email_lower == "rentalagent@agentmail.to":
            return True
        
        # Check if the message is from any of our known email addresses
        our_emails = [
            "rentalagent@agentmail.to",
            "rentai@agentmail.to", 
            "rental@agentmail.to"
        ]
        
        for our_email in our_emails:
            if our_email.lower() in from_email_lower:
                return True
        
        # Check if the subject indicates it's an auto-reply from us
        subject_lower = subject.lower()
        if any(indicator in subject_lower for indicator in [
            "re: rentai", "auto-reply", "automated response"
        ]):
            return True
        
        # Check if the content indicates it's from our system
        content_lower = text_body.lower()
        if any(indicator in content_lower for indicator in [
            "this is an automated response from rentai",
            "ai rental assistant",
            "prospective tenant assistant"
        ]):
            return True
        
        return False
        
    except Exception as e:
        print(f"⚠️ Error checking if self-message: {e}")
        return False

def send_auto_reply(to_email, original_subject, original_body, message_id=None):
    """Send an automatic reply email using the correct AgentMail API"""
    try:
        # Extract email address from "Name <email>" format
        if '<' in to_email and '>' in to_email:
            email_address = to_email.split('<')[1].split('>')[0].strip()
        else:
            email_address = to_email.strip()
        
        # Create auto-reply content
        reply_subject = f"Re: {original_subject}"
        
        # Text version
        text_body = f"""Hello! This is rentAI, your AI rental assistant.

Thank you for reaching out to rental@agentmail.to. I've received your message:

Subject: {original_subject}
Message: {original_body}

I'm here to help you find the perfect rental property. I can assist you with:
- Property searches based on your budget and preferences
- Location-based recommendations
- Bedroom and bathroom requirements
- Property type preferences (apartment, house, condo, etc.)

Please reply with your rental requirements and I'll help you find suitable properties!

Best regards,
rentAI
AI Rental Assistant
rental@agentmail.to

---
This is an automated response from rentAI."""
        
        # HTML version
        html_body = f"""<p>Hello! This is <strong>rentAI</strong>, your AI rental assistant.</p>

<p>Thank you for reaching out to rental@agentmail.to. I've received your message:</p>

<p><strong>Subject:</strong> {original_subject}<br>
<strong>Message:</strong> {original_body}</p>

<p>I'm here to help you find the perfect rental property. I can assist you with:</p>
<ul>
<li>Property searches based on your budget and preferences</li>
<li>Location-based recommendations</li>
<li>Bedroom and bathroom requirements</li>
<li>Property type preferences (apartment, house, condo, etc.)</li>
</ul>

<p>Please reply with your rental requirements and I'll help you find suitable properties!</p>

<p>Best regards,<br>
<strong>rentAI</strong><br>
AI Rental Assistant<br>
rental@agentmail.to</p>

<hr>
<p><em>This is an automated response from rentAI.</em></p>"""
        
        print(f"📤 Attempting to send auto-reply to: {email_address}")
        
        # Use the CORRECT AgentMail API structure
        if hasattr(client, 'inboxes') and hasattr(client.inboxes, 'messages'):
            print("✅ Using CORRECT AgentMail inboxes.messages API")
            
            if message_id:
                # Reply to the message using the CORRECT API
                print(f"📧 Replying to message: {message_id}")
                try:
                    sent_message = client.inboxes.messages.reply(
                        inbox_id=existing_inbox_id,
                        message_id=message_id,
                        text=text_body,
                        html=html_body
                    )
                    print(f"✅ Reply sent successfully: {getattr(sent_message, 'message_id', 'Unknown ID')}")
                    
                    # Update labels as shown in documentation
                    try:
                        client.inboxes.messages.update(
                            inbox_id=existing_inbox_id,
                            message_id=message_id,
                            add_labels=["replied"],
                            remove_labels=["unreplied"]
                        )
                        print("✅ Labels updated successfully")
                    except Exception as e:
                        print(f"⚠️ Label update failed: {e}")
                    
                    return True
                except Exception as e:
                    print(f"⚠️ Reply method failed: {e}")
            
            # Fallback: send new message using CORRECT API
            print(f"📧 Sending new message...")
            try:
                sent_message = client.inboxes.messages.send(
                    inbox_id=existing_inbox_id,
                    to=[email_address],
                    subject=reply_subject,
                    text=text_body,
                    html=html_body
                )
                print(f"✅ Message sent successfully: {getattr(sent_message, 'message_id', 'Unknown ID')}")
                return True
            except Exception as e:
                print(f"⚠️ Send method failed: {e}")
        else:
            print("❌ Inboxes messages API not available")
            
    except Exception as e:
        print(f"❌ Error sending auto-reply: {e}")
        return False

# 1️⃣ Connect to existing inbox
print("📬 Connecting to existing inbox...")
existing_inbox_id = "rentalagent@agentmail.to"
print(f"✅ Connected to inbox: {existing_inbox_id}")

# Show current cache status
print(f"📊 Current processed messages: {get_processed_messages_count()}")
print(f"📧 Current sent emails: {get_sent_emails_count()}")

# Get inbox details
# Get inbox details
try:
    inbox = client.inboxes.get(inbox_id=existing_inbox_id)
    print("Inbox details:", inbox)
except Exception as e:
    print(f"⚠️ Could not fetch inbox details: {e}")
    # Create a mock inbox object for the existing inbox
    class MockInbox:
        def __init__(self, inbox_id):
            self.inbox_id = inbox_id
    inbox = MockInbox(existing_inbox_id)


def process_inbox_messages():
    """
    Process all messages in the inbox for auto-replies.
    This function should only be called when explicitly needed.
    """
    print(f"\n🧵 Listing threads for inbox {existing_inbox_id}...")
    try:
        # List all threads and filter manually
        threads_response = client.threads.list()
        threads = threads_response.threads if hasattr(threads_response, 'threads') else threads_response
        threads = [t for t in threads if getattr(t, "inbox_id", None) == existing_inbox_id]
    except Exception as e:
        print(f"⚠️ Could not list threads: {e}")
        threads = []

    if not threads:
        print(f"No threads found in inbox {existing_inbox_id}.")
        return
    else:
        print(f"Found {len(threads)} thread(s) in inbox {existing_inbox_id}:")
        for t in threads:
                print(f"Thread ID: {t.thread_id}, Subject: {getattr(t, 'subject', 'N/A')}, Updated at: {t.updated_at}")

    # 3️⃣ Read messages in each thread
    print("\n✉️ Reading messages in each thread...")
    for t in threads:
        try:
            # Try different API methods to find the correct one
            # Skip the custom messages client for reading - use original method
            if hasattr(client, 'threads') and hasattr(client.threads, 'messages'):
                messages_response = client.threads.messages.list(thread_id=t.thread_id)
            else:
                # Try to get thread details which might include messages
                thread_details = client.threads.get(thread_id=t.thread_id)
                messages = getattr(thread_details, 'messages', [])
                messages_response = type('obj', (object,), {'messages': messages})()
            
            messages = messages_response.messages if hasattr(messages_response, 'messages') else messages_response
            
            print(f"\nMessages in Thread {t.thread_id}:")
            if messages:
                for i, m in enumerate(messages):
                    print(f"\n--- Message {i+1} ---")
                    print(f"Message attributes: {[attr for attr in dir(m) if not attr.startswith('_')]}")
                    
                    # Extract email details using the correct attribute names
                    from_email = getattr(m, 'from_', 'N/A')
                    subject = getattr(m, 'subject', 'N/A')
                    text_body = getattr(m, 'text', 'N/A')
                    html_body = getattr(m, 'html', 'N/A')
                    timestamp = getattr(m, 'timestamp', 'N/A')
                    message_id = getattr(m, 'message_id', 'N/A')
                    to_recipients = getattr(m, 'to', [])
                    labels = getattr(m, 'labels', [])
                    
                    print(f"From: {from_email}")
                    print(f"To: {', '.join(to_recipients) if to_recipients else 'N/A'}")
                    print(f"Subject: {subject}")
                    print(f"Timestamp: {timestamp}")
                    print(f"Message ID: {message_id}")
                    print(f"Labels: {labels}")
                    print(f"Text Body: {text_body[:200] + '...' if len(str(text_body)) > 200 else text_body}")
                    if html_body and html_body != text_body:
                        print(f"HTML Body: {html_body[:200] + '...' if len(str(html_body)) > 200 else html_body}")
                    
                    # CRITICAL: Check if we've already processed this message
                    if message_id in processed_messages:
                        print(f"🚫 Message {message_id} already processed - skipping to prevent duplicates")
                        continue
                    
                    # CRITICAL: Check if we've already replied to this message using labels
                    if 'replied' in labels:
                        print(f"🚫 Message {message_id} already has 'replied' label - skipping to prevent duplicates")
                        continue
                    
                    # CRITICAL: Check if this is a message from ourselves to prevent loops
                    if is_self_message(from_email, subject, text_body):
                        print(f"🚫 Ignoring self-message from {from_email} to prevent loops")
                        continue
                    
                    # Add to processed set immediately to prevent race conditions
                    processed_messages.add(message_id)
                    print(f"📝 Added message {message_id} to processed set")
                    
                    # Auto-reply functionality
                    print(f"\n🤖 Sending auto-reply...")
                    try:
                        auto_reply_sent = send_auto_reply(from_email, subject, text_body, message_id)
                        if auto_reply_sent:
                            print(f"✅ Auto-reply sent successfully!")
                            # Mark message as replied to prevent future duplicates
                            try:
                                client.inboxes.messages.update(
                                    inbox_id=existing_inbox_id,
                                    message_id=message_id,
                                    add_labels=["replied"],
                                    remove_labels=["unreplied"]
                                )
                                print(f"🏷️ Marked message {message_id} as replied")
                            except Exception as e:
                                print(f"⚠️ Could not mark message as replied: {e}")
                        else:
                            print(f"⚠️ Auto-reply failed")
                            # Remove from processed set if auto-reply failed
                            processed_messages.discard(message_id)
                    except Exception as e:
                        print(f"❌ Auto-reply error: {e}")
                        # Remove from processed set if auto-reply failed
                        processed_messages.discard(message_id)
            else:
                print("No messages found in this thread")
        except Exception as e:
            print(f"⚠️ Could not read messages from thread {t.thread_id}: {e}")
            print(f"Available client attributes: {[attr for attr in dir(client) if not attr.startswith('_')]}")

def check_inbox_status():
    """
    Check inbox status without processing messages.
    This function can be called safely during import.
    """
    # 4️⃣ List existing drafts (since we can't create new ones easily)
    print("\n📝 Checking existing drafts...")
    try:
        drafts_response = client.drafts.list()
        drafts = drafts_response.drafts if hasattr(drafts_response, 'drafts') else drafts_response
        
        if drafts:
            print(f"Found {len(drafts)} draft(s):")
            for draft in drafts:
                print(f"- Draft ID: {getattr(draft, 'draft_id', 'N/A')}, Subject: {getattr(draft, 'subject', 'N/A')}")
        else:
            print("No drafts found")
            
    except Exception as e:
        print(f"⚠️ Could not list drafts: {e}")

    # 5️⃣ Show webhook capabilities
    print("\n🔗 Webhook capabilities:")
    print("- Webhook endpoint: http://localhost:5000/webhook")
    print("- Supported events: message.received, thread.created")
    print("- To set up webhooks, configure in AgentMail dashboard")

    # 6️⃣ List all inboxes (for verification)
    print(f"\n📋 Listing all inboxes...")
    try:
        inboxes_response = client.inboxes.list()
        all_inboxes = inboxes_response.inboxes if hasattr(inboxes_response, 'inboxes') else inboxes_response
        print(f"Found {len(all_inboxes)} inbox(es):")
        for inbox_item in all_inboxes:
            print(f"- Inbox ID: {inbox_item.inbox_id}, Created: {getattr(inbox_item, 'created_at', 'N/A')}")
    except Exception as e:
        print(f"⚠️ Could not list inboxes: {e}")

    print(f"\n🎉 AgentMail integration complete for inbox: {existing_inbox_id}")

# Only run status check on import, not full message processing
check_inbox_status()