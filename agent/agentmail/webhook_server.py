"""
AgentMail Webhook Server
=======================

This module provides a FastAPI webhook server to handle AgentMail events
like message.received and thread.created for real-time email processing.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import our AgentMail integration
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from realtor import RentalOrchestrator, MessageData

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AgentMail Webhook Server",
    description="Handles AgentMail webhook events for rental assistant",
    version="1.0.0"
)

# Initialize the rental orchestrator
try:
    orchestrator = RentalOrchestrator()
    logger.info("✅ Rental Orchestrator initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Rental Orchestrator: {e}")
    orchestrator = None

# Track processed messages to prevent spam - GLOBAL SET
processed_messages = set()

def log_processed_messages():
    """Log current state of processed messages for debugging"""
    logger.info(f"📊 Current processed messages count: {len(processed_messages)}")
    if processed_messages:
        logger.info(f"📋 Processed message IDs: {list(processed_messages)[:5]}...")  # Show first 5

class WebhookEvent(BaseModel):
    """AgentMail webhook event structure"""
    event_type: str
    inbox_id: str
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    timestamp: datetime
    data: Dict[str, Any]

class WebhookResponse(BaseModel):
    """Webhook response structure"""
    status: str
    message: str
    processed_at: datetime

@app.get("/")
async def root():
    """Root endpoint with webhook information"""
    return {
        "service": "AgentMail Webhook Server",
        "status": "running",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "events": "/events",
            "docs": "/docs"
        },
        "supported_events": [
            "message.received",
            "thread.created"
        ],
        "inbox": "rentalagent@agentmail.to"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_status": "initialized" if orchestrator else "failed"
    }

@app.get("/processed-messages")
async def get_processed_messages():
    """Get current state of processed messages for debugging"""
    return {
        "processed_count": len(processed_messages),
        "processed_messages": list(processed_messages),
        "status": "active"
    }

@app.post("/webhook", response_model=WebhookResponse)
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle AgentMail webhook events
    
    Supported events:
    - message.received: New message received
    - thread.created: New conversation thread created
    """
    try:
        # Get raw request body
        body = await request.body()
        logger.info(f"📨 Received webhook with {len(body)} bytes")
        
        # Try to parse as JSON
        try:
            webhook_data = json.loads(body.decode('utf-8'))
            logger.info(f"📋 Webhook data: {json.dumps(webhook_data, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse webhook JSON: {e}")
            logger.info(f"Raw body: {body}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Extract event information - AgentMail webhook format
        event_type = webhook_data.get("event", webhook_data.get("event_type", "unknown"))
        inbox_id = webhook_data.get("inbox_id", "unknown")
        
        # For message.received events, the message data is nested
        if event_type == "message.received" and "message" in webhook_data:
            message_data = webhook_data["message"]
            message_id = message_data.get("id", message_data.get("message_id", "unknown"))
            thread_id = message_data.get("thread_id", "unknown")
        else:
            message_id = webhook_data.get("message_id", webhook_data.get("id", "unknown"))
            thread_id = webhook_data.get("thread_id", "unknown")
        
        logger.info(f"📨 Event type: {event_type}")
        logger.info(f"📧 Inbox: {inbox_id}")
        logger.info(f"🆔 Message ID: {message_id}")
        logger.info(f"🧵 Thread ID: {thread_id}")
        
        # Create a WebhookEvent object for processing
        event = WebhookEvent(
            event_type=event_type,
            inbox_id=inbox_id,
            message_id=message_id,
            thread_id=thread_id,
            timestamp=datetime.now(),
            data=webhook_data
        )
        
        # Process the event in the background
        background_tasks.add_task(process_webhook_event, event)
        
        return WebhookResponse(
            status="accepted",
            message=f"Event {event_type} queued for processing",
            processed_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

async def process_webhook_event(event: WebhookEvent):
    """
    Process webhook events in the background
    
    This function handles the actual processing of webhook events
    and integrates with the rental assistant system.
    """
    try:
        logger.info(f"🔄 Processing webhook event: {event.event_type}")
        
        if not orchestrator:
            logger.error("❌ Orchestrator not available")
            return
        
        if event.event_type == "message.received":
            await handle_message_received(event)
        elif event.event_type == "thread.created":
            await handle_thread_created(event)
        else:
            logger.warning(f"⚠️ Unsupported event type: {event.event_type}")
            
    except Exception as e:
        logger.error(f"❌ Error processing webhook event: {e}")

async def handle_message_received(event: WebhookEvent):
    """Handle message.received events"""
    try:
        logger.info(f"📬 Processing new message: {event.message_id}")
        
        # Extract message data from the webhook event
        message_data = extract_message_data_from_event(event)
        
        if message_data:
            # CRITICAL: Check if this is a message from ourselves to prevent loops
            if is_self_message_webhook(message_data):
                logger.info(f"🚫 Ignoring self-message from {message_data.from_email} to prevent loops")
                return
            
            # Check if this is a test message (fake message ID) - process it anyway
            if (event.message_id.startswith("test_") or 
                event.message_id.startswith("webhook_test_") or 
                event.message_id.startswith("spam_test_") or 
                event.message_id.startswith("rental_inquiry_") or 
                event.message_id.startswith("simulation_test_")):
                logger.info(f"🧪 Test message detected: {event.message_id}")
                
                # Still check if already processed to prevent spam
                if event.message_id in processed_messages:
                    logger.info(f"🚫 Test message {event.message_id} already processed - skipping")
                    return
                
                # Add to processed set and log
                processed_messages.add(event.message_id)
                logger.info(f"📝 Added test message {event.message_id} to processed set")
                logger.info(f"✅ Test message processed successfully: {event.message_id}")
                logger.info(f"📧 From: {message_data.from_email}")
                logger.info(f"📝 Subject: {message_data.subject}")
                logger.info(f"💬 Content: {message_data.text_content[:100]}...")
                logger.info(f"🚀 Processing test message with Gemini AI (will send as new message)")
                
                # Process test messages through the rental assistant (will send as new message)
                success = orchestrator.communication_agent.process_incoming_message(message_data)
                
                if success:
                    logger.info(f"✅ Successfully processed test message {event.message_id}")
                else:
                    logger.error(f"❌ Failed to process test message {event.message_id}")
                return
            
            # CRITICAL: Check if we've already processed this message (in-memory tracking)
            logger.info(f"🔍 Checking if message {event.message_id} is already processed...")
            log_processed_messages()
            
            if event.message_id in processed_messages:
                logger.info(f"🚫 Message {event.message_id} already processed - skipping to prevent spam")
                return
            
            # Add to processed messages immediately to prevent race conditions
            processed_messages.add(event.message_id)
            logger.info(f"📝 Added message {event.message_id} to processed set")
            log_processed_messages()
            
            # Process real messages through the rental assistant
            success = orchestrator.communication_agent.process_incoming_message(message_data)
            
            if success:
                logger.info(f"✅ Successfully processed message {event.message_id}")
                # Try to mark as replied in AgentMail (but don't fail if it doesn't work)
                try:
                    await mark_message_as_replied(event.message_id, event.inbox_id)
                except Exception as e:
                    logger.warning(f"⚠️ Could not mark message as replied in AgentMail: {e}")
                    logger.info(f"✅ Message still tracked in memory to prevent spam")
            else:
                logger.error(f"❌ Failed to process message {event.message_id}")
                # Remove from processed set if processing failed
                processed_messages.discard(event.message_id)
        else:
            logger.warning(f"⚠️ Could not extract message data from event {event.message_id}")
            
    except Exception as e:
        logger.error(f"❌ Error handling message.received: {e}")

async def handle_thread_created(event: WebhookEvent):
    """Handle thread.created events"""
    try:
        logger.info(f"🧵 Processing new thread: {event.thread_id}")
        
        # For new threads, we might want to:
        # 1. Initialize conversation context
        # 2. Send a welcome message
        # 3. Set up tracking
        
        logger.info(f"✅ Thread {event.thread_id} created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error handling thread.created: {e}")

async def check_if_already_replied(message_id: str, inbox_id: str) -> bool:
    """Check if we've already replied to this message using labels"""
    try:
        if not orchestrator:
            return False
            
        # Get the message to check its labels using AgentMail API
        message = orchestrator.mail_manager.client.inboxes.messages.get(
            inbox_id=inbox_id,
            message_id=message_id
        )
        
        # Check if 'replied' label exists
        labels = getattr(message, 'labels', [])
        has_replied = 'replied' in labels
        
        logger.info(f"🏷️ Message {message_id} labels: {labels}")
        logger.info(f"🔍 Has 'replied' label: {has_replied}")
        
        return has_replied
        
    except Exception as e:
        logger.warning(f"⚠️ Could not check labels for message {message_id}: {e}")
        return False

async def mark_message_as_replied(message_id: str, inbox_id: str):
    """Mark a message as replied using labels"""
    try:
        if not orchestrator:
            return
            
        # Use the AgentMail update_message_labels method
        success = orchestrator.mail_manager.update_message_labels(
            message_id=message_id,
            add_labels=["replied"],
            remove_labels=["unreplied"]
        )
        
        if success:
            logger.info(f"🏷️ Marked message {message_id} as replied")
        else:
            logger.warning(f"⚠️ Failed to mark message {message_id} as replied")
        
    except Exception as e:
        logger.warning(f"⚠️ Could not mark message {message_id} as replied: {e}")

def is_self_message_webhook(message_data: MessageData) -> bool:
    """Check if this message is from ourselves to prevent reply loops"""
    try:
        from_email = message_data.from_email.lower().strip()
        
        # Check if the message is from our own email address
        if from_email == "rentalagent@agentmail.to":
            return True
        
        # Check if the message is from any of our known email addresses
        our_emails = [
            "rentalagent@agentmail.to",
            "rentai@agentmail.to", 
            "rental@agentmail.to"
        ]
        
        for our_email in our_emails:
            if our_email.lower() in from_email:
                return True
        
        # Check if the subject indicates it's an auto-reply from us
        subject = message_data.subject.lower()
        if any(indicator in subject for indicator in [
            "re: rentai", "auto-reply", "automated response"
        ]):
            return True
        
        # Check if the content indicates it's from our system
        content = message_data.text_content.lower()
        if any(indicator in content for indicator in [
            "this is an automated response from rentai",
            "ai rental assistant",
            "prospective tenant assistant"
        ]):
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"⚠️ Error checking if self-message: {e}")
        return False

def extract_message_data_from_event(event: WebhookEvent) -> Optional[MessageData]:
    """
    Extract MessageData from webhook event
    
    This function converts the webhook event data into our internal
    MessageData structure for processing.
    """
    try:
        # Extract data from the event
        event_data = event.data
        
        # For AgentMail webhooks, message data might be nested
        if "message" in event_data:
            message_info = event_data["message"]
        else:
            message_info = event_data
        
        # Create MessageData object with proper AgentMail field mapping
        message_data = MessageData(
            message_id=event.message_id or "unknown",
            thread_id=event.thread_id or "unknown",
            from_email=message_info.get("from", message_info.get("from_email", "unknown@example.com")),
            to_emails=message_info.get("to", message_info.get("to_emails", [])),
            subject=message_info.get("subject", "No Subject"),
            text_content=message_info.get("text", message_info.get("text_content", "")),
            html_content=message_info.get("html", message_info.get("html_content")),
            timestamp=event.timestamp,
            labels=message_info.get("labels", [])
        )
        
        logger.info(f"📧 Extracted message from: {message_data.from_email}")
        logger.info(f"📝 Subject: {message_data.subject}")
        logger.info(f"💬 Content preview: {message_data.text_content[:100]}...")
        
        return message_data
        
    except Exception as e:
        logger.error(f"❌ Error extracting message data: {e}")
        return None

@app.post("/test-webhook")
async def test_webhook():
    """
    Test endpoint to simulate webhook events
    
    This endpoint allows you to test the webhook functionality
    without needing actual AgentMail events.
    """
    try:
        # Create a test event
        test_event = WebhookEvent(
            event_type="message.received",
            inbox_id="rentalagent@agentmail.to",
            message_id="test_message_123",
            thread_id="test_thread_456",
            timestamp=datetime.now(),
            data={
                "from": "test@example.com",
                "to": ["rentalagent@agentmail.to"],
                "subject": "Test Rental Inquiry",
                "text": "Hi, I'm looking for a 2-bedroom apartment in downtown area. My budget is $2000/month.",
                "html": "<p>Hi, I'm looking for a 2-bedroom apartment in downtown area. My budget is $2000/month.</p>",
                "labels": ["inquiry", "rental"]
            }
        )
        
        # Process the test event
        await process_webhook_event(test_event)
        
        return {
            "status": "success",
            "message": "Test webhook event processed (simulation mode)",
            "note": "This was a test message - no actual reply sent to AgentMail",
            "test_event": test_event.dict(),
            "what_would_happen": "With a real message, rentAI would send an auto-reply with property recommendations"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in test webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Test webhook failed: {str(e)}")

@app.post("/simulate-real-message")
async def simulate_real_message():
    """
    Simulate what would happen with a real message (without sending actual replies)
    """
    try:
        # Extract message data from the test event
        test_event = WebhookEvent(
            event_type="message.received",
            inbox_id="rentalagent@agentmail.to",
            message_id="simulation_test_123",
            thread_id="simulation_thread_456",
            timestamp=datetime.now(),
            data={
                "from": "prospect@example.com",
                "to": ["rentalagent@agentmail.to"],
                "subject": "Looking for 3BR Apartment Downtown",
                "text": "Hello! I am interested in viewing a 3-bedroom apartment. My budget is $2500/month and I prefer downtown location. When can I schedule a viewing?",
                "html": "<p>Hello! I am interested in viewing a 3-bedroom apartment. My budget is $2500/month and I prefer downtown location. When can I schedule a viewing?</p>",
                "labels": ["inquiry", "rental", "urgent"]
            }
        )
        
        message_data = extract_message_data_from_event(test_event)
        
        if message_data and orchestrator:
            # Generate the auto-reply content (without sending it)
            text_body, html_body = orchestrator.communication_agent.generate_auto_reply(message_data)
            
            return {
                "status": "success",
                "message": "Simulated real message processing",
                "original_message": {
                    "from": message_data.from_email,
                    "subject": message_data.subject,
                    "content": message_data.text_content
                },
                "generated_reply": {
                    "subject": f"Re: {message_data.subject}",
                    "text_preview": text_body[:200] + "...",
                    "html_preview": html_body[:200] + "..."
                },
                "note": "This shows what rentAI would send as an auto-reply to a real inquiry"
            }
        else:
            return {"error": "Could not process simulation"}
            
    except Exception as e:
        logger.error(f"❌ Error in simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting AgentMail Webhook Server...")
    logger.info("📡 Webhook endpoint: http://localhost:5001/webhook")
    logger.info("📚 API docs: http://localhost:5001/docs")
    logger.info("🧪 Test endpoint: http://localhost:5001/test-webhook")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5001,
        log_level="info"
    )
