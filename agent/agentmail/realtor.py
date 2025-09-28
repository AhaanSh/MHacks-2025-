"""
Autonomous AI Rental Assistant - AgentMail Integration
=====================================================

This module provides the core AgentMail integration for the rental assistant,
handling email communication, message processing, and autonomous responses.
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from agentmail import AgentMail, SendMessageRequest, ReplyToMessageRequest, UpdateMessageRequest

# Add gemini directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gemini'))
from gemini_service import GeminiEmailService, EmailContext

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MessageData:
    """Structured message data"""
    message_id: str
    thread_id: str
    from_email: str
    to_emails: List[str]
    subject: str
    text_content: str
    html_content: Optional[str]
    timestamp: datetime
    labels: List[str]

@dataclass
class ConversationContext:
    """Context for ongoing conversations"""
    property_id: Optional[str]
    user_preferences: Dict[str, Any]
    conversation_history: List[MessageData]
    current_status: str
    last_updated: datetime

class AgentMailManager:
    """Manages AgentMail API interactions with proper error handling"""
    
    def __init__(self, api_key: str):
        """Initialize AgentMail client"""
        self.client = AgentMail(api_key=api_key)
        self.inbox_id = "rentalagent@agentmail.to"
        logger.warning(f"AgentMail initialized: {self.inbox_id}")
    
    def get_inbox_details(self) -> Dict[str, Any]:
        """Get inbox details"""
        try:
            inbox = self.client.inboxes.get(inbox_id=self.inbox_id)
            return {
                "inbox_id": inbox.inbox_id,
                "created_at": getattr(inbox, 'created_at', None),
                "status": "active"
            }
        except Exception as e:
            logger.warning(f"Could not fetch inbox details: {e}")
            return {"inbox_id": self.inbox_id, "status": "unknown"}
    
    def list_threads(self) -> List[Dict[str, Any]]:
        """List all threads in the inbox"""
        try:
            threads_response = self.client.inboxes.threads.list(inbox_id=self.inbox_id)
            threads = threads_response.threads if hasattr(threads_response, 'threads') else threads_response

            inbox_threads = []
            for thread in threads:
                inbox_threads.append({
                    "thread_id": thread.thread_id,
                    "subject": getattr(thread, 'subject', 'N/A'),
                    "updated_at": thread.updated_at,
                    "message_count": getattr(thread, 'message_count', 0)
                })

            logger.warning(f"Found {len(inbox_threads)} threads")
            return inbox_threads
            
        except Exception as e:
            logger.error(f"Could not list threads: {e}")
            return []
    
    def get_thread_messages(self, thread_id: str) -> List[MessageData]:
        """Get all messages in a thread"""
        try:
            thread = self.client.inboxes.threads.get(inbox_id=self.inbox_id, thread_id=thread_id)
            messages = getattr(thread, 'messages', [])
            
            message_data = []
            for msg in messages:
                message_data.append(MessageData(
                    message_id=getattr(msg, 'message_id', 'N/A'),
                    thread_id=thread_id,
                    from_email=getattr(msg, 'from_', 'N/A'),
                    to_emails=getattr(msg, 'to', []),
                    subject=getattr(msg, 'subject', 'N/A'),
                    text_content=getattr(msg, 'text', 'N/A'),
                    html_content=getattr(msg, 'html', None),
                    timestamp=getattr(msg, 'timestamp', datetime.now()),
                    labels=getattr(msg, 'labels', [])
                ))
            
            # Messages retrieved successfully
            return message_data
            
        except Exception as e:
            logger.error(f"Could not get messages from thread {thread_id}: {e}")
            return []
    
    def send_message(self, to_emails: List[str], subject: str, text_content: str, 
                    html_content: Optional[str] = None, labels: List[str] = None) -> bool:
        """Send a new message"""
        try:
            request = SendMessageRequest(
                inbox_id=self.inbox_id,
                to=to_emails,
                subject=subject,
                text=text_content,
                html=html_content,
                labels=labels or []
            )
            
            response = self.client.inboxes.messages.send(**request.model_dump())
            logger.warning(f"Message sent: {getattr(response, 'message_id', 'Unknown ID')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def reply_to_message(self, message_id: str, text_content: str, 
                        html_content: Optional[str] = None) -> bool:
        """Reply to an existing message"""
        try:
            request = ReplyToMessageRequest(
                inbox_id=self.inbox_id,
                message_id=message_id,
                text=text_content,
                html=html_content
            )
            
            response = self.client.inboxes.messages.reply(**request.model_dump())
            logger.warning(f"Reply sent: {getattr(response, 'message_id', 'Unknown ID')}")
            
            # Update labels
            self.update_message_labels(message_id, add_labels=["replied"], remove_labels=["unreplied"])
            return True
            
        except Exception as e:
            logger.error(f"Failed to reply to message {message_id}: {e}")
            return False
    
    def update_message_labels(self, message_id: str, add_labels: List[str] = None, 
                            remove_labels: List[str] = None) -> bool:
        """Update message labels"""
        try:
            request = UpdateMessageRequest(
                inbox_id=self.inbox_id,
                message_id=message_id,
                add_labels=add_labels or [],
                remove_labels=remove_labels or []
            )
            
            self.client.inboxes.messages.update(**request.model_dump())
            # Labels updated
            return True
            
        except Exception as e:
            logger.warning(f"Label update failed for message {message_id}: {e}")
            return False

class RentalCommunicationAgent:
    """Handles autonomous rental communication"""
    
    def __init__(self, agent_mail_manager: AgentMailManager):
        self.mail_manager = agent_mail_manager
        self.conversations: Dict[str, ConversationContext] = {}
        
        # Initialize Gemini service
        try:
            # Load Gemini API key from gemini directory
            gemini_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gemini', '.env')
            from dotenv import load_dotenv
            load_dotenv(gemini_env_path)
            
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if gemini_api_key:
                self.gemini_service = GeminiEmailService(gemini_api_key)
                logger.warning("✅ Gemini AI service initialized for intelligent responses")
            else:
                logger.warning("⚠️ GEMINI_API_KEY not found, using fallback responses")
                self.gemini_service = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Gemini service: {e}")
            self.gemini_service = None
        
        logger.warning("Rental Communication Agent initialized")
    
    def generate_auto_reply(self, original_message: MessageData) -> tuple[str, str]:
        """Generate auto-reply content using Gemini AI"""
        
        # Check if we have Gemini service available
        if self.gemini_service:
            try:
                # Create email context for Gemini
                email_context = EmailContext(
                    from_email=original_message.from_email,
                    subject=original_message.subject,
                    content=original_message.text_content,
                    timestamp=original_message.timestamp,
                    thread_id=original_message.thread_id,
                    message_id=original_message.message_id
                )
                
                # Generate intelligent response using Gemini
                text_body, html_body = self.gemini_service.generate_rental_response(email_context)
                logger.warning(f"✅ Generated Gemini-powered response for {original_message.from_email}")
                return text_body, html_body
                
            except Exception as e:
                logger.warning(f"⚠️ Gemini response generation failed: {e}, using fallback")
        
        # Fallback to default response if Gemini is not available or fails
        return self._generate_fallback_response(original_message)
    
    def _generate_fallback_response(self, original_message: MessageData) -> tuple[str, str]:
        """Generate fallback auto-reply content"""
        # Extract email address from "Name <email>" format
        from_email = original_message.from_email
        if '<' in from_email and '>' in from_email:
            email_address = from_email.split('<')[1].split('>')[0].strip()
        else:
            email_address = from_email.strip()
        
        reply_subject = f"Re: {original_message.subject}"
        
        # Text version
        text_body = f"""Hello! This is rentAI, a prospective tenant assistant.

Thank you for your message about rental properties:

Subject: {original_message.subject}
Message: {original_message.text_content}

I'm interested in learning more about your available rental properties. I'm looking for:
- Properties that match my budget and preferences
- Good locations with convenient amenities
- Suitable bedroom and bathroom configurations
- Properties that meet my specific needs

Could you please provide more details about your available rentals? I'd love to schedule a viewing if possible!

Best regards,
rentAI
Prospective Tenant Assistant
rentalagent@agentmail.to

---
This is an automated response from rentAI."""
        
        # HTML version
        html_body = f"""<p>Hello! This is <strong>rentAI</strong>, a prospective tenant assistant.</p>

<p>Thank you for your message about rental properties:</p>

<p><strong>Subject:</strong> {original_message.subject}<br>
<strong>Message:</strong> {original_message.text_content}</p>

<p>I'm interested in learning more about your available rental properties. I'm looking for:</p>
<ul>
<li>Properties that match my budget and preferences</li>
<li>Good locations with convenient amenities</li>
<li>Suitable bedroom and bathroom configurations</li>
<li>Properties that meet my specific needs</li>
</ul>

<p>Could you please provide more details about your available rentals? I'd love to schedule a viewing if possible!</p>

<p>Best regards,<br>
<strong>rentAI</strong><br>
Prospective Tenant Assistant<br>
rentalagent@agentmail.to</p>

<hr>
<p><em>This is an automated response from rentAI.</em></p>"""
        
        return text_body, html_body
    
    def process_incoming_message(self, message: MessageData) -> bool:
        """Process an incoming message and send auto-reply"""
        try:
            logger.warning(f"Processing message from {message.from_email}")
            
            # CRITICAL: Check if this is a message from ourselves to prevent loops
            if self._is_self_message(message):
                logger.warning(f"🚫 Ignoring self-message from {message.from_email} to prevent loops")
                return True
            
            # Check if we've already replied to this message to prevent duplicates
            if self._has_already_replied(message):
                logger.warning(f"⚠️ Already replied to message {message.message_id}, skipping")
                return True
            
            # Update conversation context
            self.update_conversation_context(message.thread_id, message)
            
            # Generate auto-reply using Gemini AI
            text_body, html_body = self.generate_auto_reply(message)
            
            # Try to send reply first
            success = self.mail_manager.reply_to_message(
                message_id=message.message_id,
                text_content=text_body,
                html_content=html_body
            )
            
            if success:
                logger.warning(f"✅ Auto-reply sent to {message.from_email}")
                # Mark as replied to prevent future duplicates
                self._mark_as_replied(message)
                return True
            else:
                # If reply fails (e.g., message not found), try sending as new message
                logger.warning(f"⚠️ Reply failed, trying to send as new message to {message.from_email}")
                
                # Create reply subject
                reply_subject = f"Re: {message.subject}" if not message.subject.startswith("Re:") else message.subject
                
                # Send as new message
                success = self.mail_manager.send_message(
                    to_emails=[message.from_email],
                    subject=reply_subject,
                    text_content=text_body,
                    html_content=html_body,
                    labels=["auto-reply", "gemini-ai"]
                )
                
                if success:
                    logger.warning(f"✅ Auto-reply sent as new message to {message.from_email}")
                    # Mark as replied to prevent future duplicates
                    self._mark_as_replied(message)
                    return True
                else:
                    logger.error(f"❌ Failed to send auto-reply as new message to {message.from_email}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return False
    
    def _is_self_message(self, message: MessageData) -> bool:
        """Check if this message is from ourselves to prevent reply loops"""
        try:
            from_email = message.from_email.lower().strip()
            
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
            subject = message.subject.lower()
            if any(indicator in subject for indicator in [
                "re: rentai", "auto-reply", "automated response"
            ]):
                return True
            
            # Check if the content indicates it's from our system
            content = message.text_content.lower()
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

    def _has_already_replied(self, message: MessageData) -> bool:
        """Check if we've already replied to this message"""
        try:
            # Check if message has 'replied' label
            if 'replied' in message.labels:
                return True
            
            # Check conversation context for recent replies
            if message.thread_id in self.conversations:
                context = self.conversations[message.thread_id]
                # If we've already processed messages in this thread recently, skip
                if context.current_status == "replied":
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking reply status: {e}")
            return False
    
    def _mark_as_replied(self, message: MessageData):
        """Mark message as replied to prevent future duplicates"""
        try:
            # Update conversation context
            if message.thread_id in self.conversations:
                self.conversations[message.thread_id].current_status = "replied"
            
            # Update labels in AgentMail
            self.mail_manager.update_message_labels(
                message_id=message.message_id,
                add_labels=["replied"],
                remove_labels=["unreplied"]
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error marking message as replied: {e}")
    
    def update_conversation_context(self, thread_id: str, message: MessageData):
        """Update conversation context"""
        if thread_id not in self.conversations:
            self.conversations[thread_id] = ConversationContext(
                property_id=None,
                user_preferences={},
                conversation_history=[],
                current_status="initial",
                last_updated=datetime.now()
            )
        
        self.conversations[thread_id].conversation_history.append(message)
        self.conversations[thread_id].last_updated = datetime.now()

class RentalOrchestrator:
    """Main orchestrator for the rental assistant system"""
    
    def __init__(self):
        """Initialize the rental orchestrator"""
        load_dotenv()
        api_key = os.getenv("AGENTMAIL_API_KEY")
        
        if not api_key:
            raise ValueError("❌ AGENTMAIL_API_KEY not found in .env")
        
        self.mail_manager = AgentMailManager(api_key)
        self.communication_agent = RentalCommunicationAgent(self.mail_manager)
        logger.warning("Rental Orchestrator initialized")
    
    def run_email_monitoring(self):
        """Main loop for monitoring and processing emails"""
        logger.warning("Starting email monitoring...")
        
        # List and process threads
        threads = self.mail_manager.list_threads()
        
        if not threads:
            logger.warning("No threads found")
            return
        
        logger.warning(f"Processing {len(threads)} threads...")
        
        for thread_info in threads:
            thread_id = thread_info["thread_id"]
            
            # Get messages in thread
            messages = self.mail_manager.get_thread_messages(thread_id)
            
            if not messages:
                continue
            
            # Process each message
            for message in messages:
                # Update conversation context
                self.communication_agent.update_conversation_context(thread_id, message)
                
                # Process and send auto-reply
                self.communication_agent.process_incoming_message(message)
        
        logger.warning("Email monitoring complete")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of all conversations"""
        return {
            "total_conversations": len(self.communication_agent.conversations),
            "active_threads": len(self.mail_manager.list_threads()),
            "conversations": {
                thread_id: {
                    "status": context.current_status,
                    "message_count": len(context.conversation_history),
                    "last_updated": context.last_updated.isoformat(),
                    "property_id": context.property_id
                }
                for thread_id, context in self.communication_agent.conversations.items()
            }
        }

def main():
    """Main entry point"""
    try:
        orchestrator = RentalOrchestrator()
        orchestrator.run_email_monitoring()
        
        # Print summary
        summary = orchestrator.get_conversation_summary()
        logger.warning(f"Session Summary: {summary}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()