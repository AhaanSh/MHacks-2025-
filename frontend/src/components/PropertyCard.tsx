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
        className={`featured-card transition-all duration-300 cursor-pointer ${
          isExpanded ? 'ring-1 ring-primary/20' : ''
        }`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* High-quality imagery area - design.md emphasis on visual-first */}
        <div className="aspect-video bg-gradient-to-br from-primary/10 to-accent/10 relative overflow-hidden">
          <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
            <div className="text-white/80 text-center">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <MapPin className="w-8 h-8" />
              </div>
              <p className="text-sm font-medium">High-res Property Image</p>
            </div>
          </div>
          {/* Status badge overlay */}
          <div className="absolute top-4 right-4">
            <Badge className={`${getStatusColor(property.statusColor)} shadow-sm`}>
              {property.statusText}
            </Badge>
          </div>
        </div>
        
        <CardHeader className="pb-4">
          <div className="space-y-3">
            <div>
              <h3 className="text-heading text-lg font-semibold mb-1">
                {property.address}
              </h3>
              <p className="text-3xl font-bold text-primary">${property.rent.toLocaleString()}<span className="text-lg text-muted font-normal">/mo</span></p>
            </div>
            <p className="text-sm text-muted">{property.lastActivity}</p>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex gap-6 text-sm text-body">
              <span className="flex items-center gap-2 font-medium">
                <Bed className="w-4 h-4 text-primary" />
                {property.bedrooms} bed
              </span>
              <span className="flex items-center gap-2 font-medium">
                <Bath className="w-4 h-4 text-primary" />
                {property.bathrooms} bath
              </span>
              <span className="flex items-center gap-2 font-medium">
                <Square className="w-4 h-4 text-primary" />
                {property.sqft} sqft
              </span>
            </div>
            <span className="text-sm text-muted font-medium">{property.landlord}</span>
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
                        {message.sender === 'ai' ? '🤖 RentAI' : `👤 ${property.landlord}`} • {message.time}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <Button 
                  onClick={(e) => {
                    e.stopPropagation();
                    handleScheduleViewing();
                  }}
                  className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
                  size="lg"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Viewing
                </Button>
                <Button 
                  variant="outline" 
                  onClick={(e) => e.stopPropagation()}
                  className="flex-1 border-primary/20 hover:bg-primary/5 text-primary font-medium"
                  size="lg"
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Contact
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