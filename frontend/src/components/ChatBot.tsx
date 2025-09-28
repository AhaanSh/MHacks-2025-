import { useState, useEffect, useRef } from "react";
import { Send, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Message {
  id: string;
  text: string;
  sender: "user" | "ai";
  timestamp: string;
  propertyInfo?: {
    address: string;
    rent: number;
    bedrooms: number;
    bathrooms: number;
  };
}

const MOCK_AI_RESPONSES = [
  "I'd be happy to help you find the perfect apartment! What's your budget range and preferred location?",
  "Based on your preferences, I found several great options. Let me show you the details.",
  "That's a great property! The location has excellent walkability and is close to public transportation.",
  "I can schedule a viewing for you this weekend. What day works best?",
  "The rental market in that area is quite competitive. I recommend acting quickly on properties you like.",
  "Let me check the latest availability and pricing for similar units in your preferred neighborhoods.",
  "This property includes utilities and has great amenities. Would you like me to negotiate the rent?",
  "I've analyzed the lease terms and they look standard. Everything seems to be in order.",
];

const PROPERTY_SUGGESTIONS = [
  { address: "789 Maple Street", rent: 1900, bedrooms: 2, bathrooms: 1 },
  { address: "456 Pine Avenue", rent: 2300, bedrooms: 3, bathrooms: 2 },
  { address: "321 Elm Drive", rent: 1750, bedrooms: 1, bathrooms: 1 },
  { address: "654 Cedar Lane", rent: 2100, bedrooms: 2, bathrooms: 2 },
];

export const ChatBot = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (!isInitialized) {
      setMessages([
        {
          id: "1",
          text: "Hi! I'm your AI apartment hunting assistant. I can help you find properties, answer questions about listings, schedule viewings, and even negotiate rent. What can I help you with today?",
          sender: "ai",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
      setIsInitialized(true);
    }
  }, [isInitialized]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateAIResponse = (userMessage: string): Message => {
    const lowerMessage = userMessage.toLowerCase();
    let response = MOCK_AI_RESPONSES[Math.floor(Math.random() * MOCK_AI_RESPONSES.length)];
    let propertyInfo = undefined;

    // Generate contextual responses based on user input
    if (lowerMessage.includes("budget") || lowerMessage.includes("price") || lowerMessage.includes("rent")) {
      response = "What's your monthly budget range? I can filter properties based on your price preferences.";
    } else if (lowerMessage.includes("bedroom") || lowerMessage.includes("bed")) {
      response = "How many bedrooms are you looking for? I have listings from studio to 3+ bedroom apartments.";
    } else if (lowerMessage.includes("location") || lowerMessage.includes("area") || lowerMessage.includes("neighborhood")) {
      response = "Which neighborhoods are you interested in? I can show you properties in different areas with various amenities.";
    } else if (lowerMessage.includes("show") || lowerMessage.includes("find") || lowerMessage.includes("search")) {
      response = "Here's a property that matches your criteria:";
      propertyInfo = PROPERTY_SUGGESTIONS[Math.floor(Math.random() * PROPERTY_SUGGESTIONS.length)];
    } else if (lowerMessage.includes("schedule") || lowerMessage.includes("viewing") || lowerMessage.includes("visit")) {
      response = "I can schedule a viewing for you! What day and time work best? I'll coordinate with the landlord.";
    } else if (lowerMessage.includes("negotiate") || lowerMessage.includes("lower") || lowerMessage.includes("deal")) {
      response = "I can help negotiate the rent! Based on market analysis, there might be room for a 5-10% reduction. Should I reach out to the landlord?";
    }

    return {
      id: Date.now().toString(),
      text: response,
      sender: "ai",
      timestamp: new Date().toLocaleTimeString(),
      propertyInfo,
    };
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: "user",
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    // Simulate AI thinking time
    setTimeout(() => {
      const aiResponse = generateAIResponse(inputValue);
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, Math.random() * 2000 + 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-4xl mx-auto">
      {/* Chat Header */}
      <div className="border-b bg-card/50 p-4 rounded-t-lg">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary rounded-lg">
            <Bot className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">RentalBuddy AI Assistant</h2>
            <p className="text-sm text-muted-foreground">Ask me anything about apartment hunting!</p>
          </div>
          <div className="ml-auto">
            <Badge variant="default" className="animate-pulse">
              ● Active
            </Badge>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4 bg-card/20">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 animate-fade-in ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.sender === "ai" && (
                <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary-foreground" />
                </div>
              )}
              
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  message.sender === "user"
                    ? "bg-primary text-primary-foreground ml-auto"
                    : "bg-muted"
                }`}
              >
                <p className="text-sm">{message.text}</p>
                
                {message.propertyInfo && (
                  <div className="mt-3 p-3 bg-background/10 rounded border border-border/20">
                    <h4 className="font-semibold text-sm">{message.propertyInfo.address}</h4>
                    <div className="flex gap-4 text-xs text-muted-foreground mt-1">
                      <span>${message.propertyInfo.rent}/mo</span>
                      <span>{message.propertyInfo.bedrooms} bed</span>
                      <span>{message.propertyInfo.bathrooms} bath</span>
                    </div>
                    <Button size="sm" className="mt-2 text-xs h-7">
                      View Details
                    </Button>
                  </div>
                )}
                
                <div className="text-xs opacity-70 mt-1">
                  {message.timestamp}
                </div>
              </div>

              {message.sender === "user" && (
                <div className="flex-shrink-0 w-8 h-8 bg-muted rounded-full flex items-center justify-center">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3 animate-fade-in">
              <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary-foreground" />
              </div>
              <div className="bg-muted rounded-lg p-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t bg-card/50 p-4 rounded-b-lg">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about apartments, neighborhoods, pricing, or schedule a viewing..."
            className="flex-1"
            disabled={isTyping}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            size="icon"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        
        {/* Quick Action Buttons */}
        <div className="flex gap-2 mt-3 flex-wrap">
          {[
            "Show me apartments under $2000",
            "I need a 2-bedroom apartment",
            "Schedule a viewing",
            "Help me negotiate rent"
          ].map((suggestion) => (
            <Button
              key={suggestion}
              variant="outline"
              size="sm"
              className="text-xs h-7"
              onClick={() => setInputValue(suggestion)}
              disabled={isTyping}
            >
              {suggestion}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};