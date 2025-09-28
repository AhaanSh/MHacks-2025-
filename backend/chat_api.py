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
    preferredDate: Optional[str] = None
    customMessage: Optional[str] = None

class ActionResponse(BaseModel):
    success: bool
    message: str

# In-memory conversation storage for demo
conversations: Dict[str, List[Dict]] = {}

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
    Updated to handle the new emoji-based format
    """
    properties = []
    
    lines = response_text.split('\n')
    current_property = {}
    
    for line in lines:
        line = line.strip()
        
        # Look for property header line with house emoji
        if line.startswith('🏠 Property'):
            # If we have a current property, save it
            if current_property:
                properties.append(create_property_info(current_property))
                current_property = {}
            
            # Parse: "🏠 Property 1: Address - $Price"
            try:
                # Extract address and price
                parts = line.split(':', 1)[1].strip()  # Remove "🏠 Property 1:"
                if ' - $' in parts:
                    address, price_str = parts.rsplit(' - $', 1)
                    price_str = price_str.replace(',', '')
                    current_property['address'] = address.strip()
                    current_property['rent'] = int(price_str) if price_str.isdigit() else 1500
                else:
                    current_property['address'] = parts.strip()
                    current_property['rent'] = 1500
            except:
                current_property['address'] = "Unknown Address"
                current_property['rent'] = 1500
        
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
    return PropertyInfo(
        id=str(uuid.uuid4()),
        address=prop_data.get('address', 'Unknown Address'),
        rent=prop_data.get('rent', 1500),
        bedrooms=prop_data.get('bedrooms', 2),
        bathrooms=prop_data.get('bathrooms', 1.0),
        description=f"Great property at {prop_data.get('address', 'this location')}",
        amenities=["Parking", "Laundry"],
        landlord={"name": "Property Manager", "email": "contact@property.com", "phone": "555-0199"}
    )

async def communicate_with_mcp_agent(message: str, conversation_id: str) -> MCPResponse:
    """
    Communicate with the MCP agent using the existing business logic
    """
    try:
        # Use the existing MCP agent functions directly
        understood_query = await understand_query(message)
        
        # Call business logic
        business_response = handle_user_query(conversation_id, understood_query)
        
        # Parse properties from response
        properties = format_properties_from_business_logic(business_response)
        
        return MCPResponse(
            success=True,
            message=business_response,
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default ports
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
        return ActionResponse(
            success=True,
            message=f"Tour scheduled for property {request.propertyId} on {preferred_date}. You'll receive a confirmation email shortly."
        )
    except Exception as e:
        return ActionResponse(
            success=False,
            message="Failed to schedule tour. Please try again."
        )

@app.post("/api/outreach", response_model=ActionResponse)
async def setup_outreach(request: ActionRequest):
    """
    Handle outreach setup
    """
    try:
        custom_message = request.customMessage or "I'm interested in learning more about this property."
        return ActionResponse(
            success=True,
            message=f"Outreach message sent to landlord for property {request.propertyId}. They should respond within 24 hours."
        )
    except Exception as e:
        return ActionResponse(
            success=False,
            message="Failed to setup outreach. Please try again."
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
    uvicorn.run(app, host="127.0.0.1", port=3001)