import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity } from "lucide-react";

interface ActivityItem {
  icon: string;
  text: string;
  time: string;
  id: number;
}

export const ActivityFeed = () => {
  const [activities] = useState<ActivityItem[]>([]);

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
              className={`flex items-start gap-3 p-3 rounded-lg transition-all ${
                index === 0 ? 'slide-in-right bg-primary/5 border border-primary/20' : 'hover:bg-muted/50'
              }`}
            >
              <span className="text-xl flex-shrink-0">{activity.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{activity.text}</p>
                <p className="text-xs text-muted-foreground">{activity.time}</p>
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
    </Card>
  );
};