# Chatbot Communication Architecture

## Overview

This document outlines our approach for enabling communication between the frontend chatbot interface and our MCP (Model Context Protocol) agent that provides specialized rental property recommendations using Gemini AI.

**Context:** This is designed as a hackathon demo focusing on clean functionality over production concerns.

## Architecture Approach

### Current Flow
```
User → Frontend ChatBot → MCPService → FastAPI Backend → MCP Agent → Gemini + Business Logic → Response Chain Back
```

### Components

#### 1. Frontend Service Layer (`MCPService`)
- **Purpose:** Clean API abstraction for chatbot communication
- **Location:** Frontend TypeScript service class
- **Responsibilities:**
  - Send chat messages to backend
  - Handle user actions (favorite, schedule tour, outreach)
  - Manage conversation state within browser session
  - Provide graceful error handling

#### 2. FastAPI Backend Bridge
- **Purpose:** Translate HTTP requests to MCP agent communication
- **Location:** Backend API service
- **Responsibilities:**
  - Convert REST API calls to MCP `ChatMessage` protocol
  - Manage session mapping between web users and MCP conversations
  - Handle response formatting for frontend consumption

#### 3. MCP Agent Integration
- **Purpose:** Maintain specialized rental expertise and Gemini integration
- **Location:** Existing `agent/agents.py`
- **Responsibilities:**
  - Process user queries with Gemini AI
  - Apply rental-specific business logic
  - Filter hardcoded rental CSV data
  - Return property recommendations with explanations

## Technical Implementation

### Key Interfaces

```typescript
interface PropertyInfo {
  id: string;
  address: string;
  rent: number;
  bedrooms: number;
  bathrooms: number;
  description?: string;
  amenities?: string[];
  location?: { lat: number; lng: number; };
  images?: string[];
  landlord?: { name: string; email: string; phone: string; };
}

interface MCPResponse {
  success: boolean;
  message: string;
  properties?: PropertyInfo[];
  error?: string;
}
```

### Communication Protocol

1. **User Input:** User types rental requirements in chatbot
2. **Frontend Processing:** MCPService sends HTTP POST to `/api/chat`
3. **Backend Translation:** FastAPI converts to MCP `ChatMessage`
4. **Agent Processing:** MCP agent uses Gemini to understand query and filter rental data
5. **Response Chain:** Property recommendations flow back through same path
6. **User Actions:** Separate endpoints handle favorites, tours, and outreach

## Demo-Specific Considerations

### Hardcoded Elements (Acceptable for Hackathon)
- **Localhost URLs:** `http://localhost:3001/api`
- **No Authentication:** Open endpoints for demo simplicity
- **CSV Data:** Static rental property database
- **Session-Only State:** No permanent storage required
- **Simple Error Messages:** Generic fallbacks for clean demo experience

### Conversation Management
- **Session-Based:** Conversation ID tracks context within browser session
- **No Persistence:** Context resets on page refresh (acceptable for demo)
- **Memory Management:** Conversations cleaned up automatically on session end

## Potential Pitfalls & Solutions

### Demo Day Reliability Issues

#### 1. Network Dependencies
**Problem:** Gemini API calls could fail during presentation
**Solution:** 
```typescript
// Fallback response system
static getDemoResponse(message: string): MCPResponse {
  return {
    success: true,
    message: "Based on your requirements, I found some great properties...",
    properties: [/* pre-selected demo properties */]
  };
}
```

#### 2. MCP Agent Startup Time
**Problem:** Agent initialization delay
**Solution:**
- Start agent before demo begins
- Add health check endpoint: `GET /api/health`
- Implement agent status indicator in UI

#### 3. Slow API Responses
**Problem:** Gemini processing can take 3-5 seconds
**Solution:**
- Add loading animations and "AI thinking" indicators
- Pre-compute responses for common demo queries
- Set reasonable timeout limits (30 seconds)

#### 4. Conversation State Loss
**Problem:** Browser refresh loses context
**Solution:**
```typescript
// Simple session persistence
const conversationId = sessionStorage.getItem('conversationId') || 
  generateNewConversationId();
```

#### 5. Error Recovery
**Problem:** Mid-demo failures
**Solution:**
- Demo mode with pre-scripted responses
- Quick reset functionality
- Graceful degradation to hardcoded responses

### Implementation Safeguards

```typescript
export class MCPService {
  private static config = {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api',
    timeout: 30000,
    isDemoMode: process.env.NODE_ENV === 'development'
  };

  static async sendMessage(message: string, conversationId?: string): Promise<MCPResponse> {
    try {
      // Add artificial delay for demo "thinking" effect
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const response = await fetch(`${this.config.baseUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversationId }),
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
      
    } catch (error) {
      // Fallback to demo responses if needed
      if (this.config.isDemoMode && !navigator.onLine) {
        return this.getDemoResponse(message);
      }
      
      return {
        success: false,
        message: 'I\'m having trouble connecting right now. Let me try that again...',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}
```

## Future Production Considerations

If we wanted to make this production-ready, we would need to address:

### Security & Authentication
- **User Authentication:** JWT tokens, OAuth integration
- **API Security:** Rate limiting, input validation, CORS policies
- **Data Protection:** Encrypt sensitive user data, secure property information

### Scalability & Performance
- **Database Integration:** Replace CSV with PostgreSQL/MongoDB
- **Caching Layer:** Redis for conversation state and property search results
- **Load Balancing:** Multiple MCP agent instances
- **CDN Integration:** Asset delivery and API caching

### State Management
- **Persistent Storage:** User profiles, conversation history, saved properties
- **Session Management:** Distributed sessions across multiple servers
- **Real-time Updates:** WebSocket connections for live property updates

### Monitoring & Reliability
- **Error Tracking:** Comprehensive logging and alerting
- **Health Monitoring:** Service health checks and auto-recovery
- **Analytics:** User behavior tracking and performance metrics
- **Backup Systems:** Data backup and disaster recovery

### Enhanced Features
- **Real Property Data:** MLS integration, live property feeds
- **Advanced AI:** Fine-tuned models, personalization
- **Communication Systems:** Email/SMS notifications, calendar integration
- **Payment Processing:** Stripe integration for application fees

### Infrastructure Changes
- **Container Orchestration:** Docker + Kubernetes deployment
- **Environment Management:** Staging, testing, production environments
- **CI/CD Pipeline:** Automated testing and deployment
- **Configuration Management:** Environment-specific settings

## Conclusion

This architecture provides a clean, demo-ready solution that showcases the core value proposition: an AI-powered rental assistant that understands user requirements and provides intelligent property recommendations. The approach balances simplicity for demo purposes while maintaining a clear path to production scalability.

The MCP agent remains the specialized brain of the system, while the frontend service layer provides a clean interface that can evolve independently as requirements grow.