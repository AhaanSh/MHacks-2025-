/**
 * MCPService - Frontend service for communicating with MCP agent via FastAPI backend
 * Handles chat messages, property actions, and error handling for hackathon demo
 */

interface PropertyInfo {
  id: string;
  address: string;
  rent: number;
  bedrooms: number;
  bathrooms: number;
  description?: string;
  amenities?: string[];
  location?: {
    lat: number;
    lng: number;
  };
  images?: string[];
  landlord?: {
    name: string;
    email: string;
    phone: string;
  };
}

interface MCPResponse {
  success: boolean;
  message: string;
  properties?: PropertyInfo[];
  error?: string;
}

interface ChatRequest {
  message: string;
  conversationId?: string;
}

interface ActionResponse {
  success: boolean;
  message: string;
}

export class MCPService {
  private static BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api';
  private static timeout = 30000; // 30 second timeout
  private static isDemoMode = process.env.NODE_ENV === 'development';

  /**
   * Generate a new conversation ID for session tracking
   */
  static generateConversationId(): string {
    return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get conversation ID from session storage or create new one
   */
  static getConversationId(): string {
    if (typeof window === 'undefined') return this.generateConversationId();
    
    const stored = sessionStorage.getItem('mcp_conversation_id');
    if (stored) return stored;
    
    const newId = this.generateConversationId();
    sessionStorage.setItem('mcp_conversation_id', newId);
    return newId;
  }

  /**
   * Demo fallback responses for reliability during presentation
   */
  private static getDemoResponse(message: string): MCPResponse {
    const messageLower = message.toLowerCase();
    
    const demoProperties: PropertyInfo[] = [
      {
        id: "demo_1",
        address: "123 Oak Street, Downtown",
        rent: 1800,
        bedrooms: 2,
        bathrooms: 1.5,
        description: "Beautiful 2-bedroom apartment with modern amenities and city views",
        amenities: ["Parking", "Laundry", "Pet-friendly", "Gym"],
        location: { lat: 40.7589, lng: -73.9851 },
        landlord: { name: "John Smith", email: "john@oakproperties.com", phone: "555-0123" }
      },
      {
        id: "demo_2",
        address: "456 Pine Avenue, Midtown", 
        rent: 2200,
        bedrooms: 3,
        bathrooms: 2.0,
        description: "Spacious 3-bedroom with great natural light and modern kitchen",
        amenities: ["Gym", "Pool", "Parking", "Concierge"],
        location: { lat: 40.7505, lng: -73.9934 },
        landlord: { name: "Jane Doe", email: "jane@pineresidences.com", phone: "555-0456" }
      }
    ];

    if (messageLower.includes('budget') || messageLower.includes('price') || messageLower.includes('$')) {
      return {
        success: true,
        message: "I found some properties within your budget range. Here are my top recommendations based on value and location:",
        properties: demoProperties
      };
    } else if (messageLower.includes('bedroom') || messageLower.includes('bed')) {
      return {
        success: true,
        message: "Based on your bedroom requirements, here's a great option that matches your needs:",
        properties: [demoProperties[1]] // 3-bedroom
      };
    } else {
      return {
        success: true,
        message: "I'd be happy to help you find the perfect rental! Here are some popular properties that might interest you:",
        properties: [demoProperties[0]]
      };
    }
  }

  /**
   * Send a chat message to the MCP agent
   */
  static async sendMessage(message: string, conversationId?: string): Promise<MCPResponse> {
    const activeConversationId = conversationId || this.getConversationId();
    
    try {
      // Add slight delay for demo "thinking" effect
      if (this.isDemoMode) {
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          conversationId: activeConversationId,
        } as ChatRequest),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: MCPResponse = await response.json();
      
      // Store successful conversation ID
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('mcp_conversation_id', activeConversationId);
      }
      
      return data;

    } catch (error) {
      console.error('Error communicating with MCP agent:', error);
      
      // Log the actual error for debugging
      console.error('Fetch error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        url: `${this.BASE_URL}/chat`,
        error
      });
      
      // Only fallback to demo responses if we're offline - remove demo mode fallback for testing
      if (!navigator.onLine) {
        return this.getDemoResponse(message);
      }

      return {
        success: false,
        message: "I'm having trouble connecting to my knowledge base right now. Please try again in a moment.",
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Add a property to favorites
   */
  static async favoriteProperty(propertyId: string): Promise<ActionResponse> {
    try {
      const response = await fetch(`${this.BASE_URL}/favorites`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ propertyId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ActionResponse = await response.json();
      return data;

    } catch (error) {
      console.error('Error favoriting property:', error);
      return {
        success: false,
        message: 'Failed to favorite property. Please try again.',
      };
    }
  }

  /**
   * Schedule a property tour
   */
  static async scheduleTour(
    propertyId: string, 
    propertyAddress?: string,
    preferredDate?: string
  ): Promise<ActionResponse> {
    try {
      const response = await fetch(`${this.BASE_URL}/schedule-tour`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          propertyId,
          propertyAddress,
          preferredDate: preferredDate || new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ActionResponse = await response.json();
      return data;

    } catch (error) {
      console.error('Error scheduling tour:', error);
      return {
        success: false,
        message: 'Failed to schedule tour. Please try again.',
      };
    }
  }

  /**
   * Setup outreach to property landlord
   */
  static async setupOutreach(
    propertyId: string, 
    propertyAddress?: string,
    customMessage?: string
  ): Promise<ActionResponse> {
    try {
      const response = await fetch(`${this.BASE_URL}/outreach`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          propertyId,
          propertyAddress,
          customMessage: customMessage || "I'm interested in learning more about this property.",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ActionResponse = await response.json();
      return data;

    } catch (error) {
      console.error('Error setting up outreach:', error);
      return {
        success: false,
        message: 'Failed to setup outreach. Please try again.',
      };
    }
  }

  /**
   * Check if the backend service is healthy
   */
  static async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout for health check
      
      const response = await fetch(`${this.BASE_URL}/health`, {
        method: 'GET',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  /**
   * Get conversation history (for demo purposes)
   */
  static async getConversationHistory(conversationId?: string): Promise<any[]> {
    const activeConversationId = conversationId || this.getConversationId();
    
    try {
      const response = await fetch(`${this.BASE_URL}/conversations/${activeConversationId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching conversation history:', error);
      return [];
    }
  }

  /**
   * Reset conversation (clear session storage)
   */
  static resetConversation(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('mcp_conversation_id');
    }
  }
}

// Export types for use in components
export type { PropertyInfo, MCPResponse, ActionResponse };