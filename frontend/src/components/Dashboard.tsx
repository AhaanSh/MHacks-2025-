"use client";

import { useState, useEffect } from "react";
import { Bot, Home, TrendingUp, Calendar, Users, DollarSign, MapPin, Heart, Star, BarChart3, MessageCircle } from "lucide-react";
import { PropertyCard } from "./PropertyCard";
import { ActivityFeed } from "./ActivityFeed";
import { MetricsDashboard } from "./MetricsDashboard";
import { NotificationSystem } from "./NotificationSystem";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface DashboardProps {
  onNavigateToChat: () => void;
  isConnected: boolean;
}

export const Dashboard = ({ onNavigateToChat, isConnected }: DashboardProps) => {
  const [properties] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({
    totalProperties: 1247,
    favoritedProperties: 12,
    scheduledTours: 3,
    activeConversations: 2,
    avgRent: 2450,
    savedSearches: 8
  });

  return (
    <div className="min-h-screen relative">
      <NotificationSystem />
      
      {/* Dashboard Header */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-heading mb-2">Dashboard</h1>
            <p className="text-body">Track your apartment hunting progress and metrics</p>
          </div>
          <Button
            onClick={onNavigateToChat}
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <MessageCircle className="w-4 h-4 mr-2" />
            Start Chat
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="card-minimal p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                <Home className="w-6 h-6 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-heading">{dashboardStats.totalProperties.toLocaleString()}</p>
                <p className="text-sm text-muted">Available Properties</p>
              </div>
            </div>
          </div>
          
          <div className="card-minimal p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center">
                <Heart className="w-6 h-6 text-accent" />
              </div>
              <div>
                <p className="text-2xl font-bold text-heading">{dashboardStats.favoritedProperties}</p>
                <p className="text-sm text-muted">Favorited</p>
              </div>
            </div>
          </div>
          
          <div className="card-minimal p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-success/10 rounded-lg flex items-center justify-center">
                <Calendar className="w-6 h-6 text-success" />
              </div>
              <div>
                <p className="text-2xl font-bold text-heading">{dashboardStats.scheduledTours}</p>
                <p className="text-sm text-muted">Scheduled Tours</p>
              </div>
            </div>
          </div>
          
          <div className="card-minimal p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-heading">${dashboardStats.avgRent.toLocaleString()}</p>
                <p className="text-sm text-muted">Avg Rent</p>
              </div>
            </div>
          </div>
        </div>

        {/* Favorited Properties Section - Full Width */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-heading mb-6">
            Favorited Properties
          </h2>
          
          {/* Favorited properties display */}
          <div className="card-minimal p-8">
            {properties.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {properties.map((property) => (
                  <PropertyCard key={property.id} property={property} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Heart className="w-10 h-10 text-primary" />
                </div>
                <div className="space-y-4">
                  <h3 className="text-2xl font-semibold text-heading">Start Your Search</h3>
                  <p className="text-body max-w-md mx-auto">
                    Chat with our AI to discover properties tailored to your preferences and start building your favorites list.
                  </p>
                </div>
                <Button 
                  size="lg" 
                  className="h-12 px-8 bg-primary hover:bg-primary/90 text-primary-foreground mt-6"
                  onClick={onNavigateToChat}
                >
                  <MessageCircle className="w-5 h-5 mr-2" />
                  Start Chatting
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Main Dashboard Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Analytics */}
          <div className="lg:col-span-2 space-y-6">
            {/* Metrics Dashboard */}
            <div className="card-minimal p-6">
              <h3 className="text-xl font-semibold text-heading mb-4">Property Analytics</h3>
              <MetricsDashboard />
            </div>
            
            {/* Recent Properties */}
            <div className="card-minimal p-6 min-h-[400px]">
              <h3 className="text-xl font-semibold text-heading mb-4">Recent Properties</h3>
              {properties.length > 0 ? (
                <div className="space-y-4">
                  {properties.map((property) => (
                    <PropertyCard key={property.id} property={property} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                    <Home className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <p className="text-body mb-4">No recent activity yet</p>
                  <Button onClick={onNavigateToChat} variant="outline">
                    Start Searching
                  </Button>
                </div>
              )}
            </div>
          </div>
          
          {/* Right Column - Activity & Actions */}
          <div className="space-y-6">
            {/* Connection Status */}
            <div className="card-minimal p-6">
              <h3 className="text-lg font-semibold text-heading mb-4">Connection Status</h3>
              <div className="flex items-center gap-3">
                <Badge 
                  variant={isConnected ? "default" : "destructive"} 
                  className={`${isConnected ? 'bg-success text-success-foreground' : ''}`}
                >
                  {isConnected ? "● Connected" : "● Disconnected"}
                </Badge>
                <span className="text-sm text-body">
                  {isConnected ? "AI Assistant Ready" : "Reconnecting..."}
                </span>
              </div>
            </div>
            
            {/* Recent Activity */}
            <div className="card-minimal p-6">
              <h3 className="text-lg font-semibold text-heading mb-4">Recent Activity</h3>
              <ActivityFeed />
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
};