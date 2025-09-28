"use client";

import { useState, useEffect } from "react";
import { Home as HomeIcon, MessageCircle, BarChart3 } from "lucide-react";
import { Dashboard } from '../src/components/Dashboard';
import { ChatBot } from '../src/components/ChatBot';
import { HeroLanding } from '../src/components/HeroLanding';
import { AuthButton } from '../src/components/AuthButton';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function Home() {
  const [currentView, setCurrentView] = useState<"landing" | "dashboard" | "chat">("landing");
  const [isConnected, setIsConnected] = useState(true);

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

  const handleNavigateToChat = () => setCurrentView("chat");
  const handleNavigateToDashboard = () => setCurrentView("dashboard");
  const handleNavigateToLanding = () => setCurrentView("landing");

  return (
    <div className="min-h-screen relative">
      {/* Gradient Background */}
      <div 
        className="fixed inset-0 w-full h-full -z-10"
        style={{
          backgroundImage: 'url(/images/gradient-bg-hd.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      />
      {/* Global Header */}
      <header className="border-b border-border/50 bg-card/80 backdrop-blur-md sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div 
              className="flex items-center gap-4 cursor-pointer"
              onClick={handleNavigateToLanding}
            >
              <img 
                src="/rentai-logo.png" 
                alt="rentAI Logo" 
                className="h-16 w-auto"
              />
            </div>
            
            <div className="flex items-center gap-3">
              {/* View Toggle */}
              <div className="flex bg-muted rounded-lg p-1 gap-1">
                <Button
                  variant={currentView === "landing" ? "default" : "ghost"}
                  size="sm"
                  onClick={handleNavigateToLanding}
                  className="flex items-center gap-2 h-8 text-xs"
                >
                  <HomeIcon className="w-3 h-3" />
                  Home
                </Button>
                <Button
                  variant={currentView === "chat" ? "default" : "ghost"}
                  size="sm"
                  onClick={handleNavigateToChat}
                  className="flex items-center gap-2 h-8 text-xs"
                >
                  <MessageCircle className="w-3 h-3" />
                  Chat
                </Button>
                <Button
                  variant={currentView === "dashboard" ? "default" : "ghost"}
                  size="sm"
                  onClick={handleNavigateToDashboard}
                  className="flex items-center gap-2 h-8 text-xs"
                >
                  <BarChart3 className="w-3 h-3" />
                  Dashboard
                </Button>
              </div>
              
              <AuthButton />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main>
        {currentView === "landing" && (
          <HeroLanding 
            onNavigateToChat={handleNavigateToChat}
            onNavigateToDashboard={handleNavigateToDashboard}
            isConnected={isConnected}
          />
        )}
        {currentView === "chat" && <ChatBot />}
        {currentView === "dashboard" && (
          <Dashboard 
            onNavigateToChat={handleNavigateToChat}
            isConnected={isConnected}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t bg-card/70 backdrop-blur-sm mt-16">
        <div className="container mx-auto px-4 py-6 text-center text-muted-foreground">
          <p>rentAI - Made with Maize and Blue</p>
        </div>
      </footer>
    </div>
  );
}