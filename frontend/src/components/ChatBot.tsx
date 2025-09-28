import { useState, useEffect, useRef } from "react";
import { Send, Bot, User, Heart, Calendar, MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MCPService, PropertyInfo, MCPResponse } from "@/lib/mcp-service";

interface Message {
  id: string;
  text: string;
  sender: "user" | "ai";
  timestamp: string;
  properties?: PropertyInfo[];
}

export const ChatBot = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string>("");
  const [isConnected, setIsConnected] = useState<boolean>(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (!isInitialized) {
      // Initialize conversation ID
      const convId = MCPService.getConversationId();
      setConversationId(convId);
      
      // Check backend health
      MCPService.healthCheck().then(setIsConnected);
      
      // Set initial message
      setMessages([
        {
          id: "1",
          text: "Hi! I'm your AI apartment hunting assistant powered by advanced property analysis. I can help you find properties, answer questions about listings, schedule viewings, and even negotiate rent. What can I help you with today?",
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

  const handlePropertyAction = async (action: 'favorite' | 'tour' | 'outreach', propertyId: string) => {
    try {
      let result;
      switch (action) {
        case 'favorite':
          result = await MCPService.favoriteProperty(propertyId);
          break;
        case 'tour':
          result = await MCPService.scheduleTour(propertyId);
          break;
        case 'outreach':
          result = await MCPService.setupOutreach(propertyId);
          break;
      }
      
      // Add system message about the action
      const actionMessage: Message = {
        id: Date.now().toString(),
        text: result.message,
        sender: "ai",
        timestamp: new Date().toLocaleTimeString(),
      };
      
      setMessages(prev => [...prev, actionMessage]);
    } catch (error) {
      console.error('Error handling property action:', error);
    }
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
    const messageText = inputValue;
    setInputValue("");
    setIsTyping(true);

    try {
      // Send message to MCP agent via MCPService
      const response: MCPResponse = await MCPService.sendMessage(messageText, conversationId);
      
      const aiMessage: Message = {
        id: Date.now().toString(),
        text: response.message,
        sender: "ai",
        timestamp: new Date().toLocaleTimeString(),
        properties: response.properties || undefined,
      };

      setMessages(prev => [...prev, aiMessage]);
      setIsConnected(response.success);
      
    } catch (error) {
      console.error('Error sending message:', error);
      setIsConnected(false);
      
      // Add error message
      const errorMessage: Message = {
        id: Date.now().toString(),
        text: "I'm having trouble connecting right now. Please try again in a moment.",
        sender: "ai",
        timestamp: new Date().toLocaleTimeString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
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
            <p className="text-sm text-muted-foreground">Powered by MCP Agent • Ask me anything about apartment hunting!</p>
          </div>
          <div className="ml-auto">
            <Badge variant={isConnected ? "default" : "destructive"} className={isConnected ? "animate-pulse" : ""}>
              ● {isConnected ? "Connected" : "Offline"}
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
                <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                
                {message.properties && message.properties.map((property) => (
                  <div key={property.id} className="mt-3 p-3 bg-background/10 rounded border border-border/20">
                    <h4 className="font-semibold text-sm">{property.address}</h4>
                    <div className="flex gap-4 text-xs text-muted-foreground mt-1">
                      <span>${property.rent}/mo</span>
                      <span>{property.bedrooms} bed</span>
                      <span>{property.bathrooms} bath</span>
                    </div>
                    {property.description && (
                      <p className="text-xs text-muted-foreground mt-1">{property.description}</p>
                    )}
                    {property.amenities && property.amenities.length > 0 && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {property.amenities.map((amenity, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs h-5">
                            {amenity}
                          </Badge>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-2 mt-3">
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="text-xs h-7 flex items-center gap-1"
                        onClick={() => handlePropertyAction('favorite', property.id)}
                      >
                        <Heart className="w-3 h-3" />
                        Favorite
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="text-xs h-7 flex items-center gap-1"
                        onClick={() => handlePropertyAction('tour', property.id)}
                      >
                        <Calendar className="w-3 h-3" />
                        Tour
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="text-xs h-7 flex items-center gap-1"
                        onClick={() => handlePropertyAction('outreach', property.id)}
                      >
                        <MessageCircle className="w-3 h-3" />
                        Contact
                      </Button>
                    </div>
                  </div>
                ))}
                
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
            "Find properties in downtown area",
            "What's available with parking?"
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
        
        {/* Reset Conversation Button */}
        <div className="flex justify-center mt-2">
          <Button
            variant="ghost"
            size="sm"
            className="text-xs h-6 text-muted-foreground hover:text-foreground"
            onClick={() => {
              MCPService.resetConversation();
              setConversationId(MCPService.getConversationId());
              setMessages([{
                id: "1",
                text: "Hi! I'm your AI apartment hunting assistant powered by advanced property analysis. I can help you find properties, answer questions about listings, schedule viewings, and even negotiate rent. What can I help you with today?",
                sender: "ai",
                timestamp: new Date().toLocaleTimeString(),
              }]);
            }}
            disabled={isTyping}
          >
            Reset Conversation
          </Button>
        </div>
      </div>
    </div>
  );
};