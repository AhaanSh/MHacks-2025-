import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Mail, MessageCircle } from "lucide-react";
import { MessageLogsModal } from "./MessageLogsModal";

interface ActivityItem {
  id: string;
  type: string;
  icon: string;
  text: string;
  time: string;
  recipient_email?: string;
  subject?: string;
  property_info?: string;
  message_id?: string;
  timestamp?: string;
}

export const ActivityFeed = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<{
    propertyInfo: string;
    recipientEmail: string;
  } | null>(null);

  // Load activities from backend
  const loadActivities = async () => {
    try {
      // For now, we'll use mock data - in production this would call your backend API
      const mockActivities: ActivityItem[] = [
        {
          id: "msg_1_123456789",
          type: "message_sent",
          icon: "📧",
          text: "Contacted landlord123 about Property inquiry - 2 bed apartment downtown",
          time: "2:30 PM",
          recipient_email: "landlord123@example.com",
          subject: "Property inquiry - 2 bed apartment downtown",
          property_info: "2 bed apartment downtown",
          timestamp: new Date().toISOString()
        },
        {
          id: "msg_2_123456788",
          type: "message_sent", 
          icon: "📧",
          text: "Contacted realtor456 about Rental inquiry - Studio near university",
          time: "1:15 PM",
          recipient_email: "realtor456@example.com",
          subject: "Rental inquiry - Studio near university", 
          property_info: "Studio near university",
          timestamp: new Date(Date.now() - 3600000).toISOString()
        }
      ];
      setActivities(mockActivities);
    } catch (error) {
      console.error('Failed to load activities:', error);
    }
  };

  useEffect(() => {
    loadActivities();
    // Set up polling to refresh activities every 30 seconds
    const interval = setInterval(loadActivities, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="h-[600px]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          Live Activity Feed
          <div className="w-2 h-2 bg-success rounded-full animate-pulse ml-auto"></div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 max-h-[500px] overflow-y-auto">
        {activities.length > 0 ? (
          activities.map((activity, index) => (
            <div
              key={activity.id}
              className={`flex items-start gap-3 p-3 rounded-lg transition-all cursor-pointer ${
                index === 0 ? 'slide-in-right bg-primary/5 border border-primary/20' : 'hover:bg-muted/50'
              }`}
              onClick={() => {
                if (activity.type === 'message_sent' && activity.property_info && activity.recipient_email) {
                  setSelectedProperty({
                    propertyInfo: activity.property_info,
                    recipientEmail: activity.recipient_email
                  });
                }
              }}
            >
              <span className="text-xl flex-shrink-0">{activity.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{activity.text}</p>
                <div className="flex items-center justify-between mt-1">
                  <p className="text-xs text-muted-foreground">{activity.time}</p>
                  {activity.type === 'message_sent' && (
                    <MessageCircle className="w-3 h-3 text-primary opacity-50" />
                  )}
                </div>
                {activity.property_info && (
                  <p className="text-xs text-primary mt-1 font-medium">
                    📍 {activity.property_info}
                  </p>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📱</div>
            <h3 className="text-lg font-semibold mb-2">No Activity Yet</h3>
            <p className="text-muted-foreground text-sm">Activity will appear here as you interact with the AI</p>
          </div>
        )}
      </CardContent>

      {selectedProperty && (
        <MessageLogsModal
          isOpen={!!selectedProperty}
          onClose={() => setSelectedProperty(null)}
          propertyInfo={selectedProperty.propertyInfo}
          recipientEmail={selectedProperty.recipientEmail}
        />
      )}
    </Card>
  );
};