import { useState } from "react";
import { MapPin, Bed, Bath, Square, MessageCircle, Calendar, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Property {
  id: number;
  address: string;
  rent: number;
  status: string;
  statusText: string;
  statusColor: string;
  lastActivity: string;
  landlord: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  messages: Array<{ sender: string; text: string; time: string }>;
}

interface PropertyCardProps {
  property: Property;
}

export const PropertyCard = ({ property }: PropertyCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);

  const getStatusColor = (color: string) => {
    switch (color) {
      case 'success': return 'bg-success text-success-foreground';
      case 'accent': return 'bg-accent text-accent-foreground';
      case 'warning': return 'bg-warning text-warning-foreground';
      case 'primary': return 'bg-primary text-primary-foreground';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const handleScheduleViewing = () => {
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 3000);
  };

  const isPulseActive = property.status === 'viewing_scheduled' || property.status === 'negotiating';

  return (
    <>
      <Card 
        className={`transition-all duration-300 hover:shadow-lg cursor-pointer ${isPulseActive ? 'pulse-active' : ''} ${
          isExpanded ? 'ring-2 ring-primary' : ''
        }`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <CardHeader className="pb-3">
          <div className="flex justify-between items-start">
            <div className="space-y-1">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <MapPin className="w-4 h-4 text-primary" />
                {property.address}
              </h3>
              <p className="text-2xl font-bold text-primary">${property.rent.toLocaleString()}/mo</p>
            </div>
            <div className="text-right space-y-2">
              <Badge className={`${getStatusColor(property.statusColor)} status-pulse`}>
                {property.statusText}
              </Badge>
              <p className="text-sm text-muted-foreground">{property.lastActivity}</p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex justify-between items-center text-sm text-muted-foreground">
            <div className="flex gap-4">
              <span className="flex items-center gap-1">
                <Bed className="w-4 h-4" />
                {property.bedrooms} bed
              </span>
              <span className="flex items-center gap-1">
                <Bath className="w-4 h-4" />
                {property.bathrooms} bath
              </span>
              <span className="flex items-center gap-1">
                <Square className="w-4 h-4" />
                {property.sqft} sqft
              </span>
            </div>
            <span>Landlord: {property.landlord}</span>
          </div>

          {isExpanded && (
            <div className="space-y-4 fade-in-up">
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <MessageCircle className="w-4 h-4" />
                  Recent Conversation
                </h4>
                <div className="space-y-3">
                  {property.messages.map((message, index) => (
                    <div 
                      key={index}
                      className={`p-3 rounded-lg ${
                        message.sender === 'ai' 
                          ? 'bg-primary/10 border-l-4 border-primary' 
                          : 'bg-muted'
                      }`}
                    >
                      <p className="text-sm">{message.text}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {message.sender === 'ai' ? '🤖 RentalBuddy AI' : `👤 ${property.landlord}`} • {message.time}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <Button 
                  onClick={(e) => {
                    e.stopPropagation();
                    handleScheduleViewing();
                  }}
                  className="flex-1 bg-success hover:bg-success/90 text-success-foreground"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Viewing
                </Button>
                <Button 
                  variant="outline" 
                  onClick={(e) => e.stopPropagation()}
                  className="flex-1"
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Send Message
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute confetti"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                fontSize: '20px'
              }}
            >
              <Sparkles className="text-accent" />
            </div>
          ))}
        </div>
      )}
    </>
  );
};