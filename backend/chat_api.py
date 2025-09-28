"""
Chat API endpoints for MCP agent communication
Handles frontend chat requests and bridges to MCP agent
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Load environment variables from agent directory
import sys
import os
agent_path = os.path.join(os.path.dirname(__file__), '..', 'agent')
sys.path.append(agent_path)
load_dotenv(os.path.join(agent_path, '.env'))

from business_logic import handle_user_query
from agents import understand_query

# Try to import email functionality
try:
    from realtor import send_email_to_realtor
    EMAIL_AVAILABLE = True
    print("✅ Email functionality available")
except ImportError as e:
    EMAIL_AVAILABLE = False
    print(f"⚠️ Email functionality not available: {e}")

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None

class PropertyInfo(BaseModel):
    id: str
    address: str
    rent: int
    bedrooms: int
    bathrooms: float
    description: Optional[str] = None
    amenities: Optional[List[str]] = None
    location: Optional[Dict[str, float]] = None
    images: Optional[List[str]] = None
    landlord: Optional[Dict[str, str]] = None

class MCPResponse(BaseModel):
    success: bool
    message: str
    properties: Optional[List[PropertyInfo]] = None
    error: Optional[str] = None

class ActionRequest(BaseModel):
    propertyId: str
    propertyAddress: Optional[str] = None
    preferredDate: Optional[str] = None
    customMessage: Optional[str] = None

class ActionResponse(BaseModel):
    success: bool
    message: str

# In-memory conversation storage for demo
conversations: Dict[str, List[Dict]] = {}

# In-memory property ID to address mapping
property_id_to_address: Dict[str, str] = {}

# In-memory property storage for each conversation
conversation_properties: Dict[str, List[PropertyInfo]] = {}

# Demo fallback responses
DEMO_PROPERTIES = [
    {
        "id": "demo_1",
        "address": "123 Oak Street",
        "rent": 1800,
        "bedrooms": 2,
        "bathrooms": 1.5,
        "description": "Beautiful 2-bedroom apartment with modern amenities",
        "amenities": ["Parking", "Laundry", "Pet-friendly"],
        "location": {"lat": 40.7589, "lng": -73.9851},
        "landlord": {"name": "John Smith", "email": "john@example.com", "phone": "555-0123"}
    },
    {
        "id": "demo_2", 
        "address": "456 Pine Avenue",
        "rent": 2200,
        "bedrooms": 3,
        "bathrooms": 2.0,
        "description": "Spacious 3-bedroom with great natural light",
        "amenities": ["Gym", "Pool", "Parking"],
        "location": {"lat": 40.7505, "lng": -73.9934},
        "landlord": {"name": "Jane Doe", "email": "jane@example.com", "phone": "555-0456"}
    }
]

def generate_conversation_id() -> str:
    """Generate a new conversation ID"""
    return str(uuid.uuid4())

def get_demo_response(message: str) -> MCPResponse:
    """Fallback demo responses for reliability"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["budget", "price", "under", "$"]):
        return MCPResponse(
            success=True,
            message="I found some properties within your budget range. Here are my top recommendations:",
            properties=[PropertyInfo(**prop) for prop in DEMO_PROPERTIES]
        )
    elif any(word in message_lower for word in ["bedroom", "bed", "room"]):
        return MCPResponse(
            success=True,
            message="Based on your bedroom requirements, here are some great options:",
            properties=[PropertyInfo(**DEMO_PROPERTIES[1])]  # 3-bedroom
        )
    else:
        return MCPResponse(
            success=True,
            message="I'd be happy to help you find the perfect rental! Here are some popular properties:",
            properties=[PropertyInfo(**prop) for prop in DEMO_PROPERTIES[:1]]
        )

def format_properties_from_business_logic(response_text: str) -> List[PropertyInfo]:
    """
    Parse the business logic response and extract property information
    Updated to handle the actual business logic format
    """
    properties = []
    
    lines = response_text.split('\n')
    current_property = {}
    
    for line in lines:
        line = line.strip()
        
        # Look for property lines that start with "- Property"
        if line.startswith('- Property'):
            # If we have a current property, save it
            if current_property:
                properties.append(create_property_info(current_property))
                current_property = {}
            
            # Parse: "- Property 1: Address $Price | 3 bed / 2 bath | Contact: ..."
            try:
                # Extract property number first
                property_part = line.split(':', 1)[0]  # "- Property 1"
                property_number = property_part.split('Property')[1].strip()
                current_property['property_number'] = property_number
                
                # Extract the rest of the line
                rest = line.split(':', 1)[1].strip()  # Remove "- Property 1:"
                
                # Parse address and price
                if '$' in rest:
                    # Find the price part
                    price_match = None
                    for part in rest.split('|'):
                        if '$' in part:
                            price_part = part.strip()
                            # Extract price from strings like "$390,000"
                            import re
                            price_match = re.search(r'\$([\d,]+)', price_part)
                            if price_match:
                                price_str = price_match.group(1).replace(',', '')
                                current_property['rent'] = int(price_str) if price_str.isdigit() else 1500
                                break
                    
                    if not price_match:
                        current_property['rent'] = 1500
                    
                    # Extract address (everything before the first $)
                    address_part = rest.split('$')[0].strip()
                    current_property['address'] = address_part
                else:
                    current_property['address'] = rest
                    current_property['rent'] = 1500
                
                # Parse bedrooms and bathrooms
                if 'bed' in rest and 'bath' in rest:
                    bed_match = re.search(r'(\d+)\s+bed', rest)
                    bath_match = re.search(r'(\d+)\s+bath', rest)
                    if bed_match:
                        current_property['bedrooms'] = int(bed_match.group(1))
                    if bath_match:
                        current_property['bathrooms'] = int(bath_match.group(1))
                
                # Parse contact information
                if 'Contact:' in rest:
                    contact_part = rest.split('Contact:')[1].split('|')[0].strip()
                    # Extract email from contact info
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', contact_part)
                    if email_match:
                        current_property['landlord_email'] = email_match.group(1)
                    
                    # Extract phone number
                    phone_match = re.search(r'(\d{10,})', contact_part)
                    if phone_match:
                        current_property['landlord_phone'] = phone_match.group(1)
                    
                    # Extract name (first part before phone/email)
                    name_part = contact_part.split(',')[0].strip()
                    if name_part and not name_part.isdigit():
                        current_property['landlord_name'] = name_part
                
            except Exception as e:
                print(f"Error parsing property line: {e}")
                current_property['address'] = "Unknown Address"
                current_property['rent'] = 1500
                current_property['property_number'] = "?"
        
        # Look for bedroom/bathroom info
        elif '🛏️' in line and 'bed' in line:
            try:
                bed_part = line.split('🛏️')[1].split('bed')[0].strip()
                current_property['bedrooms'] = int(bed_part) if bed_part.isdigit() else 2
            except:
                current_property['bedrooms'] = 2
                
        elif '🚿' in line and 'bath' in line:
            try:
                bath_part = line.split('🚿')[1].split('bath')[0].strip()
                current_property['bathrooms'] = float(bath_part) if bath_part.replace('.', '').isdigit() else 1.0
            except:
                current_property['bathrooms'] = 1.0
        
        # Look for contact info
        elif '📞 Contact:' in line:
            contact_info = line.split('📞 Contact:', 1)[1].strip()
            current_property['contact'] = contact_info
    
    # Don't forget the last property
    if current_property:
        properties.append(create_property_info(current_property))
    
    return properties

def create_property_info(prop_data: dict) -> PropertyInfo:
    """Helper function to create PropertyInfo from parsed data"""
    property_number = prop_data.get('property_number', '?')
    address = prop_data.get('address', 'Unknown Address')
    
    # Add property number to the address display
    display_address = f"Property {property_number}: {address}"
    
    # Generate property ID and store mapping
    property_id = str(uuid.uuid4())
    property_id_to_address[property_id] = display_address
    
    # Create landlord info if available
    landlord_info = None
    if prop_data.get('landlord_email') or prop_data.get('landlord_name') or prop_data.get('landlord_phone'):
        landlord_info = {
            'name': prop_data.get('landlord_name', 'Unknown'),
            'email': prop_data.get('landlord_email', 'contact@property.com'),
            'phone': prop_data.get('landlord_phone', 'N/A')
        }
    
    return PropertyInfo(
        id=property_id,
        address=display_address,
        rent=prop_data.get('rent', 1500),
        bedrooms=prop_data.get('bedrooms', 2),
        bathrooms=prop_data.get('bathrooms', 1.0),
        description=f"Great property at {address}",
        amenities=None,
        landlord=landlord_info or {"name": "Property Manager", "email": "contact@property.com", "phone": "555-0199"}
    )

async def handle_email_request(message: str, conversation_id: str) -> MCPResponse:
    """
    Handle email requests specifically for the chat API
    """
    try:
        # Extract property number from message
        import re
        match = re.search(r'property\s+(\d+)', message.lower())
        if not match:
            return MCPResponse(
                success=False,
                message="Please specify which property number you want to email about. For example: 'send an email of interest to property 1'"
            )
        
        prop_num = int(match.group(1))
        
        # Get the stored properties for this conversation
        if conversation_id in conversation_properties:
            properties = conversation_properties[conversation_id]
            if properties and 1 <= prop_num <= len(properties):
                property_info = properties[prop_num - 1]
                
                # Extract custom message if provided
                custom_message = None
                if "saying" in message.lower():
                    saying_part = message.lower().split("saying", 1)[1].strip()
                    if saying_part:
                        custom_message = saying_part
                elif "about" in message.lower() and "property" not in message.lower().split("about", 1)[1][:20]:
                    about_part = message.lower().split("about", 1)[1].strip()
                    if about_part and "property" not in about_part[:20]:
                        custom_message = about_part
                
                # Use the email functionality if available
                if EMAIL_AVAILABLE:
                    try:
                        # Create property data structure for email function
                        property_data = {
                            "agent_email": property_info.landlord.get("email", "contact@property.com"),
                            "formattedAddress": property_info.address
                        }
                        
                        subject = f"Strong Interest in {property_info.address} - Ready to Move Forward"
                        body = custom_message or f"""Hello,

I hope this email finds you well. I am writing to express my strong interest in the property at {property_info.address}.

This property appears to be exactly what I'm looking for, and I am genuinely excited about the possibility of making it my new home. I am a serious, qualified prospective tenant with excellent references and a stable income.

I would love to:
• Schedule a viewing at your earliest convenience
• Learn more about the property's features and amenities
• Discuss the application process and requirements
• Understand the move-in timeline and any special considerations

I am ready to move quickly on this opportunity and can provide all necessary documentation promptly. Please let me know your availability for a showing, and I will make every effort to accommodate your schedule.

Thank you for your time and consideration. I look forward to hearing from you soon.

Best regards,
A Prospective Tenant

P.S. I am also happy to provide references from previous landlords and can answer any questions you might have about my background and rental history."""
                        
                        email_result = send_email_to_realtor(property_data, subject, body)
                        return MCPResponse(
                            success=True,
                            message=email_result
                        )
                    except Exception as e:
                        return MCPResponse(
                            success=False,
                            message=f"⚠️ Failed to send email: {str(e)}"
                        )
                else:
                    # Fallback when email is not available
                    agent_email = property_info.landlord.get("email", "contact@property.com")
                    return MCPResponse(
                        success=False,
                        message=f"📧 Email functionality temporarily unavailable. Please contact the agent directly at: {agent_email}"
                    )
        
        return MCPResponse(
            success=False,
            message="Please search for properties first, then try sending an email about a specific property number."
        )
        
    except Exception as e:
        return MCPResponse(
            success=False,
            message=f"Error processing email request: {str(e)}"
        )

async def communicate_with_mcp_agent(message: str, conversation_id: str) -> MCPResponse:
    """
    Communicate with the MCP agent using the existing business logic
    """
    try:
        # Check if this is an email request
        if any(phrase in message.lower() for phrase in [
            "send an email", "email the", "send email", "email about property", "send message",
            "email interest", "email of interest", "contact the landlord", "contact the agent",
            "reach out about property", "inquire about property", "express interest"
        ]):
            return await handle_email_request(message, conversation_id)
        
        # Use the existing MCP agent functions directly
        understood_query = await understand_query(message)
        
        # Add original query to the understood_query structure
        if isinstance(understood_query, dict):
            understood_query["original_query"] = message
        else:
            understood_query = {"llm_analysis": understood_query, "original_query": message}
        
        # Call business logic
        business_response = handle_user_query(conversation_id, understood_query)
        
        # Parse properties from response
        properties = format_properties_from_business_logic(business_response)
        
        # Store properties for this conversation
        if properties:
            conversation_properties[conversation_id] = properties
            clean_message = f"I found {len(properties)} properties that match your request. You can favorite, tour, or contact any of these properties using the buttons below."
        else:
            # For non-property responses (like contact info), return the business response directly
            clean_message = business_response
        
        return MCPResponse(
            success=True,
            message=clean_message,
            properties=properties if properties else None
        )
        
    except Exception as e:
        print(f"Error communicating with MCP agent: {e}")
        # Fallback to demo response
        return get_demo_response(message)

# FastAPI endpoints
app = FastAPI()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],  # Next.js ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat", response_model=MCPResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint that communicates with MCP agent
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversationId or generate_conversation_id()
        
        # Store conversation in memory for demo
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # Add user message to conversation history
        conversations[conversation_id].append({
            "role": "user",
            "message": request.message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Get response from MCP agent
        response = await communicate_with_mcp_agent(request.message, conversation_id)
        
        # Add AI response to conversation history
        conversations[conversation_id].append({
            "role": "assistant", 
            "message": response.message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return response
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return MCPResponse(
            success=False,
            message="I'm having trouble processing your request right now. Please try again.",
            error=str(e)
        )

@app.post("/api/favorites", response_model=ActionResponse)
async def favorite_property(request: ActionRequest):
    """
    Handle property favoriting
    """
    try:
        # For demo, just return success
        return ActionResponse(
            success=True,
            message=f"Property {request.propertyId} has been added to your favorites!"
        )
    except Exception as e:
        return ActionResponse(
            success=False,
            message="Failed to favorite property. Please try again."
        )

@app.post("/api/schedule-tour", response_model=ActionResponse)
async def schedule_tour(request: ActionRequest):
    """
    Handle tour scheduling
    """
    try:
        preferred_date = request.preferredDate or "next week"
        # Extract property number and address for message
        # Try to get address from mapping, fallback to provided address or ID
        property_address = (request.propertyAddress or 
                          property_id_to_address.get(request.propertyId) or 
                          f"Property {request.propertyId}")
        return ActionResponse(
            success=True,
            message=f"Request for Tour Message sent to Property: {property_address}!"
        )
    except Exception as e:
        return ActionResponse(
            success=False,
            message="Failed to schedule tour. Please try again."
        )

@app.post("/api/outreach", response_model=ActionResponse)
async def setup_outreach(request: ActionRequest):
    """
    Handle outreach setup - send email of interest to property
    """
    try:
        if not EMAIL_AVAILABLE:
            return ActionResponse(
                success=False,
                message="Email functionality not available. Please try again later."
            )
        
        # Get property information from conversation properties
        property_info = None
        if request.propertyId in conversation_properties:
            properties = conversation_properties[request.propertyId]
            if properties:
                property_info = properties[0]  # Use first property if multiple
        else:
            # Try to find property by ID in all conversations
            for conv_id, props in conversation_properties.items():
                for prop in props:
                    if prop.id == request.propertyId:
                        property_info = prop
                        break
                if property_info:
                    break
        
        if not property_info:
            return ActionResponse(
                success=False,
                message=f"Property {request.propertyId} not found. Please search for properties first."
            )
        
        # Create email subject and body
        property_address = property_info.address
        subject = f"Strong Interest in {property_address} - Ready to Move Forward"
        
        custom_message = request.customMessage or f"""Hello,

I hope this email finds you well. I am writing to express my strong interest in the property at {property_address}.

This property appears to be exactly what I'm looking for, and I am genuinely excited about the possibility of making it my new home. I am a serious, qualified prospective tenant with excellent references and a stable income.

I would love to:
• Schedule a viewing at your earliest convenience
• Learn more about the property's features and amenities
• Discuss the application process and requirements
• Understand the move-in timeline and any special considerations

I am ready to move quickly on this opportunity and can provide all necessary documentation promptly. Please let me know your availability for a showing, and I will make every effort to accommodate your schedule.

Thank you for your time and consideration. I look forward to hearing from you soon.

Best regards,
A Prospective Tenant

P.S. I am also happy to provide references from previous landlords and can answer any questions you might have about my background and rental history."""
        
        # Convert PropertyInfo to dictionary format expected by send_email_to_realtor
        property_data = {
            "agent_email": property_info.landlord.get("email", "contact@property.com"),
            "formattedAddress": property_info.address
        }
        
        # Send the email
        result = send_email_to_realtor(property_data, subject, custom_message)
        
        if "✅" in result:
            return ActionResponse(
                success=True,
                message=f"Expression of Interest Message sent to Property: {property_address}!"
            )
        else:
            return ActionResponse(
                success=False,
                message=f"Failed to send email: {result}"
            )
            
    except Exception as e:
        return ActionResponse(
            success=False,
            message=f"Failed to setup outreach: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for demo reliability
    """
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history for demo purposes
    """
    return conversations.get(conversation_id, [])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)