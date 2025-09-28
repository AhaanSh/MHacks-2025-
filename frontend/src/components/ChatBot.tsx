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
    <div className="flex flex-col h-[calc(100vh-120px)] max-w-5xl mx-auto relative">
      {/* Minimalist Chat Header - design.md style */}
      <div className="card-minimal border-0 p-6 rounded-t-xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6 text-primary-foreground" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-heading">AI Assistant</h2>
            <p className="text-body text-sm">Ready to help you find your perfect home</p>
          </div>
          <div>
            <Badge 
              variant={isConnected ? "default" : "destructive"} 
              className={`${isConnected ? 'bg-success text-success-foreground' : ''} shadow-sm`}
            >
              {isConnected ? "● Connected" : "● Offline"}
            </Badge>
          </div>
        </div>
      </div>

      {/* Clean Messages Area */}
      <ScrollArea className="flex-1 p-6 bg-background/50">
        <div className="space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 fade-in-up ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.sender === "ai" && (
                <div className="flex-shrink-0 w-10 h-10 bg-primary rounded-full flex items-center justify-center shadow-sm">
                  <Bot className="w-5 h-5 text-primary-foreground" />
                </div>
              )}
              
              <div
                className={`max-w-[75%] rounded-xl p-4 shadow-sm ${
                  message.sender === "user"
                    ? "bg-primary text-primary-foreground ml-auto"
                    : "bg-card border border-border/50"
                }`}
              >
                <p className={`leading-relaxed ${
                  message.sender === "user" ? "text-primary-foreground" : "text-body"
                }`}>{message.text}</p>
                
                {/* Rich, interactive listing cards - design.md style */}
                {message.properties && message.properties.map((property) => (
                  <div key={property.id} className="mt-4 card-minimal p-4 border border-primary/10">
                    <div className="space-y-3">
                      <div>
                        <h4 className="font-semibold text-heading">{property.address}</h4>
                        <p className="text-lg font-bold text-primary">${property.rent}<span className="text-sm text-muted font-normal">/mo</span></p>
                      </div>
                      
                      <div className="flex gap-4 text-sm text-body">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 bg-primary rounded-full"></span>
                          {property.bedrooms} bed
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 bg-primary rounded-full"></span>
                          {property.bathrooms} bath
                        </span>
                      </div>
                      
                      {property.description && (
                        <p className="text-sm text-body leading-relaxed">{property.description}</p>
                      )}
                      
                      {property.amenities && property.amenities.length > 0 && (
                        <div className="flex gap-2 flex-wrap">
                          {property.amenities.map((amenity, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs bg-accent/10 text-accent border-accent/20">
                              {amenity}
                            </Badge>
                          ))}
                        </div>
                      )}
                      
                      {/* Clear call-to-action buttons */}
                      <div className="flex gap-2 pt-2">
                        <Button 
                          size="sm" 
                          className="bg-primary hover:bg-primary/90 text-primary-foreground flex items-center gap-2"
                          onClick={() => handlePropertyAction('favorite', property.id)}
                        >
                          <Heart className="w-4 h-4" />
                          Favorite
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          className="border-accent/20 hover:bg-accent/5 text-accent flex items-center gap-2"
                          onClick={() => handlePropertyAction('tour', property.id)}
                        >
                          <Calendar className="w-4 h-4" />
                          Tour
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          className="border-primary/20 hover:bg-primary/5 text-primary flex items-center gap-2"
                          onClick={() => handlePropertyAction('outreach', property.id)}
                        >
                          <MessageCircle className="w-4 h-4" />
                          Contact
                        </Button>
                      </div>
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

      {/* Clean Input Area */}
      <div className="card-minimal border-0 p-6 rounded-b-xl">
        <div className="flex gap-3">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about apartments, neighborhoods, pricing, or schedule a viewing..."
            className="flex-1 search-focus border-border/50 h-12 text-base"
            disabled={isTyping}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            size="lg"
            className="h-12 px-6 bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <Send className="w-5 h-5" />
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