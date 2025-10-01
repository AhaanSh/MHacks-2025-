"""
Gemini AI Service for Email Response Generation
==============================================

This service integrates with Google's Gemini AI to generate intelligent
responses to rental inquiries, with duplicate prevention to save credits.
"""

import os
import logging
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from dotenv import load_dotenv
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EmailContext:
    """Context for email processing"""
    from_email: str
    subject: str
    content: str
    timestamp: datetime
    thread_id: str
    message_id: str

class GeminiResponseCache:
    """Cache to prevent duplicate Gemini API calls and save credits"""
    
    def __init__(self, cache_duration_hours: int = 24):
        self.cache = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)
        logger.info(f"Initialized Gemini response cache with {cache_duration_hours}h duration")
    
    def _generate_cache_key(self, email_context: EmailContext) -> str:
        """Generate a unique cache key based on email content"""
        # Create hash from sender, subject, and content
        content_hash = hashlib.md5(
            f"{email_context.from_email}:{email_context.subject}:{email_context.content}".encode()
        ).hexdigest()
        return f"gemini_response_{content_hash}"
    
    def get_cached_response(self, email_context: EmailContext) -> Optional[str]:
        """Check if we have a cached response for this email"""
        cache_key = self._generate_cache_key(email_context)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = cached_data['timestamp']
            
            # Check if cache is still valid
            if datetime.now() - cache_time < self.cache_duration:
                logger.info(f"✅ Using cached Gemini response for {email_context.from_email}")
                return cached_data['response']
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
                logger.info(f"🗑️ Expired cache entry removed for {email_context.from_email}")
        
        return None
    
    def cache_response(self, email_context: EmailContext, response: str):
        """Cache a Gemini response"""
        cache_key = self._generate_cache_key(email_context)
        self.cache[cache_key] = {
            'response': response,
            'timestamp': datetime.now(),
            'from_email': email_context.from_email,
            'subject': email_context.subject
        }
        logger.info(f"💾 Cached Gemini response for {email_context.from_email}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        valid_entries = 0
        expired_entries = 0
        
        now = datetime.now()
        for entry in self.cache.values():
            if now - entry['timestamp'] < self.cache_duration:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600
        }

class GeminiEmailService:
    """Service for generating intelligent email responses using Gemini AI"""
    
    def __init__(self, api_key: str):
        """Initialize Gemini service"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        self.cache = GeminiResponseCache()
        
        logger.info("✅ Gemini AI service initialized")
    
    def generate_rental_response(self, email_context: EmailContext) -> tuple[str, str]:
        """
        Generate an intelligent response to a rental inquiry using Gemini AI
        
        Returns:
            tuple: (text_response, html_response)
        """
        try:
            # Check cache first to save credits
            cached_response = self.cache.get_cached_response(email_context)
            if cached_response:
                # Convert cached response to both text and HTML formats
                return self._format_cached_response(cached_response)
            
            # Generate prompt for Gemini
            prompt = self._create_rental_prompt(email_context)
            
            logger.info(f"🤖 Generating Gemini response for {email_context.from_email}")
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            gemini_response = response.text
            
            # Cache the response to prevent duplicate API calls
            self.cache.cache_response(email_context, gemini_response)
            
            # Format the response
            text_response, html_response = self._format_response(gemini_response, email_context)
            
            logger.info(f"✅ Gemini response generated and cached for {email_context.from_email}")
            return text_response, html_response
            
        except Exception as e:
            logger.error(f"❌ Error generating Gemini response: {e}")
            # Fallback to default response
            return self._generate_fallback_response(email_context)
    
    def _create_rental_prompt(self, email_context: EmailContext) -> str:
        """Create a prompt for Gemini to generate responses as a prospective tenant"""
        return f"""
You are rentAI, an AI assistant representing a prospective tenant looking for rental properties. You respond to rental inquiries from landlords/property managers on behalf of a tenant.

INCOMING EMAIL:
From: {email_context.from_email}
Subject: {email_context.subject}
Content: {email_context.content}

TASK:
Generate a response as a prospective tenant interested in rental properties. Be professional but express interest as someone looking to rent.

GUIDELINES:
1. Respond as a prospective tenant looking for properties
2. Express interest in viewing/learning more about available properties
3. Ask relevant questions about the property (rent, location, amenities, etc.)
4. Show enthusiasm for finding the right rental
5. Be professional but personable
6. Ask about next steps (viewing, application process, etc.)

RESPONSE FORMAT:
Write a natural, conversational response that sounds like an interested prospective tenant. Do not include any formatting markers or special characters - just plain text that can be used in an email.

Make sure to:
- Respond as someone looking to rent (not someone offering rentals)
- Express genuine interest in properties
- Ask relevant tenant questions
- Be enthusiastic about finding the right place
- Ask about viewing opportunities or next steps
"""

    def _format_response(self, gemini_response: str, email_context: EmailContext) -> tuple[str, str]:
        """Format Gemini response into email-ready text and HTML"""
        
        # Extract email address from sender
        from_email = email_context.from_email
        if '<' in from_email and '>' in from_email:
            email_address = from_email.split('<')[1].split('>')[0].strip()
        else:
            email_address = from_email.strip()
        
        # Create text version
        text_body = f"""{gemini_response}

Best regards,
rentAI
Prospective Tenant Assistant
rentalagent@agentmail.to

---
This is an automated response from rentAI."""
        
        # Create HTML version
        html_body = f"""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="color: #2c3e50; margin: 0;">rentAI Response</h2>
    </div>
    
    <div style="line-height: 1.6; color: #333;">
        {gemini_response.replace(chr(10), '<br>')}
    </div>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
        <p><strong>Best regards,</strong><br>
        rentAI<br>
        Prospective Tenant Assistant<br>
        <a href="mailto:rentalagent@agentmail.to">rentalagent@agentmail.to</a></p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <p style="font-size: 12px; color: #999;">This is an automated response from rentAI.</p>
    </div>
</div>"""
        
        return text_body, html_body
    
    def _format_cached_response(self, cached_response: str) -> tuple[str, str]:
        """Format cached response for email use"""
        # Simple formatting for cached responses
        text_response = f"""{cached_response}

Best regards,
rentAI
Prospective Tenant Assistant
rentalagent@agentmail.to

---
This is an automated response from rentAI."""
        
        html_response = f"""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="line-height: 1.6; color: #333;">
        {cached_response.replace(chr(10), '<br>')}
    </div>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
        <p><strong>Best regards,</strong><br>
        rentAI<br>
        Prospective Tenant Assistant<br>
        <a href="mailto:rentalagent@agentmail.to">rentalagent@agentmail.to</a></p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <p style="font-size: 12px; color: #999;">This is an automated response from rentAI.</p>
    </div>
</div>"""
        
        return text_response, html_response
    
    def _generate_fallback_response(self, email_context: EmailContext) -> tuple[str, str]:
        """Generate a fallback response if Gemini fails"""
        text_body = f"""Hello! This is rentAI, a prospective tenant assistant.

Thank you for your message about rental properties:

Subject: {email_context.subject}
Message: {email_context.content[:200]}{'...' if len(email_context.content) > 200 else ''}

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
        
        html_body = f"""<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="color: #2c3e50; margin: 0;">rentAI Response</h2>
    </div>
    
    <div style="line-height: 1.6; color: #333;">
        <p>Hello! This is <strong>rentAI</strong>, your AI rental assistant.</p>
        
        <p>Thank you for reaching out to rentalagent@agentmail.to. I've received your message:</p>
        
        <p><strong>Subject:</strong> {email_context.subject}<br>
        <strong>Message:</strong> {email_context.content[:200]}{'...' if len(email_context.content) > 200 else ''}</p>
        
        <p>I'm here to help you find the perfect rental property. I can assist you with:</p>
        <ul>
            <li>Property searches based on your budget and preferences</li>
            <li>Location-based recommendations</li>
            <li>Bedroom and bathroom requirements</li>
            <li>Property type preferences (apartment, house, condo, etc.)</li>
        </ul>
        
        <p>Please reply with your rental requirements and I'll help you find suitable properties!</p>
    </div>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
        <p><strong>Best regards,</strong><br>
        rentAI<br>
        Prospective Tenant Assistant<br>
        <a href="mailto:rentalagent@agentmail.to">rentalagent@agentmail.to</a></p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <p style="font-size: 12px; color: #999;">This is an automated response from rentAI.</p>
    </div>
</div>"""
        
        return text_body, html_body
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        return self.cache.get_cache_stats()

def main():
    """Test the Gemini service"""
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return
    
    # Initialize service
    service = GeminiEmailService(api_key)
    
    # Create test email context
    test_context = EmailContext(
        from_email="test@example.com",
        subject="Looking for 2-bedroom apartment",
        content="Hi, I'm looking for a 2-bedroom apartment in downtown area. My budget is $2000/month.",
        timestamp=datetime.now(),
        thread_id="test_thread_123",
        message_id="test_message_456"
    )
    
    # Test response generation
    print("🧪 Testing Gemini response generation...")
    text_response, html_response = service.generate_rental_response(test_context)
    
    print("\n📧 Generated Text Response:")
    print("=" * 50)
    print(text_response)
    
    print(f"\n📊 Cache Stats: {service.get_cache_stats()}")
    
    # Test caching (should use cached response)
    print("\n🔄 Testing cache (should use cached response)...")
    text_response2, html_response2 = service.generate_rental_response(test_context)
    
    print(f"\n📊 Cache Stats After Second Call: {service.get_cache_stats()}")

if __name__ == "__main__":
    main()
