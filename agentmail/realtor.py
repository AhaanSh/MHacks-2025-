"""
Autonomous AI Rental Assistant - AgentMail Integration
=====================================================

This module provides the core AgentMail integration for the rental assistant,
handling email communication, message processing, and autonomous responses.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from agentmail import AgentMail, SendMessageRequest, ReplyToMessageRequest, UpdateMessageRequest

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
        logger.warning("Rental Communication Agent initialized")
    
    def generate_auto_reply(self, original_message: MessageData) -> tuple[str, str]:
        """Generate auto-reply content"""
        # Extract email address from "Name <email>" format
        from_email = original_message.from_email
        if '<' in from_email and '>' in from_email:
            email_address = from_email.split('<')[1].split('>')[0].strip()
        else:
            email_address = from_email.strip()
        
        reply_subject = f"Re: {original_message.subject}"
        
        # Text version
        text_body = f"""Hello! This is rentAI, your AI rental assistant.

Thank you for reaching out to rentalagent@agentmail.to. I've received your message:

Subject: {original_message.subject}
Message: {original_message.text_content}

I'm here to help you find the perfect rental property. I can assist you with:
- Property searches based on your budget and preferences
- Location-based recommendations
- Bedroom and bathroom requirements
- Property type preferences (apartment, house, condo, etc.)

Please reply with your rental requirements and I'll help you find suitable properties!

Best regards,
rentAI
AI Rental Assistant
rentalagent@agentmail.to

---
This is an automated response from rentAI."""
        
        # HTML version
        html_body = f"""<p>Hello! This is <strong>rentAI</strong>, your AI rental assistant.</p>

<p>Thank you for reaching out to rentalagent@agentmail.to. I've received your message:</p>

<p><strong>Subject:</strong> {original_message.subject}<br>
<strong>Message:</strong> {original_message.text_content}</p>

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
rentalagent@agentmail.to</p>

<hr>
<p><em>This is an automated response from rentAI.</em></p>"""
        
        return text_body, html_body
    
    def process_incoming_message(self, message: MessageData) -> bool:
        """Process an incoming message and send auto-reply"""
        try:
            # Generate auto-reply
            text_body, html_body = self.generate_auto_reply(message)
            
            # Send reply
            success = self.mail_manager.reply_to_message(
                message_id=message.message_id,
                text_content=text_body,
                html_content=html_body
            )
            
            if success:
                logger.warning(f"Auto-reply sent to {message.from_email}")
                return True
            else:
                logger.error(f"Failed to send auto-reply to {message.from_email}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False
    
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