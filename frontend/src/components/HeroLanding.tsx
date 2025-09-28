"use client";

import { useState } from "react";
import { Bot, Search, Heart, Calendar, MessageCircle, Star, Shield, Zap } from "lucide-react";
import { SearchBar } from "./SearchBar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface HeroLandingProps {
  onNavigateToChat: () => void;
  onNavigateToDashboard: () => void;
  isConnected: boolean;
}

export const HeroLanding = ({ onNavigateToChat, onNavigateToDashboard, isConnected }: HeroLandingProps) => {
  const [searchResults, setSearchResults] = useState([]);

  const handleSearch = (query: string) => {
    // Redirect to chat with the search query
    onNavigateToChat();
  };

  return (
    <div className="min-h-screen relative">
      {/* Hero Search Section - Prominent and Central */}
      <section className="text-center py-20">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="space-y-6">
            <h1 className="text-6xl font-bold text-heading mb-6">
              Find Your Perfect Home
            </h1>
            <p className="text-xl text-body max-w-2xl mx-auto leading-relaxed">
              Let AI handle the search, negotiations, and paperwork while you focus on finding your dream apartment.
            </p>
          </div>
          
          {/* Prominent Search Bar */}
          <div className="max-w-2xl mx-auto">
            <SearchBar onSearch={handleSearch} />
          </div>
          
          {/* Quick Action Buttons */}
          <div className="flex justify-center gap-4 flex-wrap mt-8">
            <Button
              size="lg"
              className="h-12 px-8 bg-primary hover:bg-primary/90 text-primary-foreground"
              onClick={onNavigateToChat}
            >
              <MessageCircle className="w-5 h-5 mr-2" />
              Start Chatting
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="h-12 px-8"
              onClick={onNavigateToDashboard}
            >
              View Dashboard
            </Button>
          </div>
        </div>
      </section>


      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-heading mb-4">
            Why Choose rentAI?
          </h2>
          <p className="text-xl text-body max-w-2xl mx-auto">
            Our AI-powered platform makes apartment hunting effortless and efficient.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="card-minimal p-8 text-center hover-warm">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Zap className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold text-heading mb-4">AI-Powered Search</h3>
            <p className="text-body">
              Our advanced AI understands your preferences and finds properties that match your exact needs.
            </p>
          </div>
          
          {/* Feature 2 */}
          <div className="card-minimal p-8 text-center hover-warm">
            <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <MessageCircle className="w-8 h-8 text-accent" />
            </div>
            <h3 className="text-xl font-semibold text-heading mb-4">Real-time Chat</h3>
            <p className="text-body">
              Chat directly with our AI assistant to get instant answers about properties, neighborhoods, and pricing.
            </p>
          </div>
          
          {/* Feature 3 */}
          <div className="card-minimal p-8 text-center hover-warm">
            <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Shield className="w-8 h-8 text-success" />
            </div>
            <h3 className="text-xl font-semibold text-heading mb-4">Secure & Reliable</h3>
            <p className="text-body">
              Your data is protected with enterprise-grade security while you search for your perfect home.
            </p>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="bg-card/50 py-16">
        <div className="max-w-4xl mx-auto text-center px-6">
          <div className="space-y-6">
            <h2 className="text-4xl font-bold text-heading">
              Ready to Find Your Dream Home or Apartment?
            </h2>
            <p className="text-xl text-body">
              Find your perfect abode with rentAI.
            </p>
            <div className="flex justify-center gap-4">
              <Button
                size="lg"
                className="h-14 px-8 bg-primary hover:bg-primary/90 text-primary-foreground text-lg"
                onClick={onNavigateToChat}
              >
                <MessageCircle className="w-6 h-6 mr-2" />
                Start Your Search
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};