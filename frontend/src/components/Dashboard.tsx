"use client";

import { useState, useEffect } from "react";
import { Bot, Wifi, WifiOff, MessageCircle, BarChart3 } from "lucide-react";
import { SearchBar } from "./SearchBar";
import { PropertyCard } from "./PropertyCard";
import { ActivityFeed } from "./ActivityFeed";
import { MetricsDashboard } from "./MetricsDashboard";
import { NotificationSystem } from "./NotificationSystem";
import { ChatBot } from "./ChatBot";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
export const Dashboard = () => {
  const [properties] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isConnected, setIsConnected] = useState(true);
  const [currentView, setCurrentView] = useState<"dashboard" | "chat">("chat");

  // Mock WebSocket connection status
  useEffect(() => {
    const interval = setInterval(() => {
      // Occasionally simulate connection issues (just for demo)
      if (Math.random() > 0.95) {
        setIsConnected(false);
        setTimeout(() => setIsConnected(true), 3000);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const handleSearch = (query: string) => {
    // Simulate search by just returning all properties
    setSearchResults(properties);
  };

  return (
    <div className="min-h-screen bg-background">
      <NotificationSystem />
      
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary rounded-lg">
                <Bot className="w-8 h-8 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  RentalBuddy
                </h1>
                <p className="text-sm text-muted-foreground">AI-Powered Apartment Hunting</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {/* View Toggle */}
              <div className="flex bg-muted rounded-lg p-1">
                <Button
                  variant={currentView === "chat" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCurrentView("chat")}
                  className="flex items-center gap-2 h-8"
                >
                  <MessageCircle className="w-4 h-4" />
                  Chat
                </Button>
                <Button
                  variant={currentView === "dashboard" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setCurrentView("dashboard")}
                  className="flex items-center gap-2 h-8"
                >
                  <BarChart3 className="w-4 h-4" />
                  Dashboard
                </Button>
              </div>
              
              <Badge variant={isConnected ? "default" : "destructive"} className="flex items-center gap-2">
                {isConnected ? (
                  <>
                    <Wifi className="w-3 h-3" />
                    Connected
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3 h-3" />
                    Reconnecting...
                  </>
                )}
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {currentView === "chat" ? (
          <ChatBot />
        ) : (
          <div className="space-y-8">
            {/* Search Section */}
            <section className="text-center space-y-4">
              <div className="max-w-3xl mx-auto">
                <h2 className="text-4xl font-bold mb-2">Find Your Perfect Home</h2>
                <p className="text-xl text-muted-foreground mb-8">
                  Let AI handle the search, negotiations, and paperwork while you focus on finding your dream apartment.
                </p>
                <SearchBar onSearch={handleSearch} />
              </div>
            </section>

            {/* Metrics Dashboard */}
            <section>
              <h3 className="text-2xl font-semibold mb-6 flex items-center gap-2">
                📊 Your Dashboard Overview
              </h3>
              <MetricsDashboard />
            </section>

            {/* Main Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Property Conversations */}
              <div className="lg:col-span-2 space-y-6">
                <h3 className="text-2xl font-semibold flex items-center gap-2">
                  🏠 Active Property Conversations
                </h3>
                <div className="space-y-4">
                  {searchResults.length > 0 ? (
                    searchResults.map((property) => (
                      <PropertyCard key={property.id} property={property} />
                    ))
                  ) : (
                    <div className="text-center py-12 border-2 border-dashed border-muted-foreground/25 rounded-lg">
                      <div className="text-6xl mb-4">🏠</div>
                      <h3 className="text-xl font-semibold mb-2">No Properties Yet</h3>
                      <p className="text-muted-foreground mb-4">Start chatting with the AI to find your perfect rental!</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Activity Feed */}
              <div className="space-y-6">
                <ActivityFeed />
                
                {/* Mock Document Upload Area */}
                <div className="border-2 border-dashed border-primary/20 rounded-lg p-6 text-center hover:border-primary/40 transition-colors">
                  <div className="space-y-2">
                    <div className="text-4xl">📄</div>
                    <h4 className="font-semibold">Upload Documents</h4>
                    <p className="text-sm text-muted-foreground">
                      Drag documents here for AI analysis
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t bg-card/50 mt-16">
        <div className="container mx-auto px-4 py-6 text-center text-muted-foreground">
          <p>RentalBuddy Dashboard - Prototype Demo</p>
        </div>
      </footer>
    </div>
  );
};