import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, Mail, MessageSquare, Calendar, CheckCircle, Target } from "lucide-react";

export const MetricsDashboard = () => {
  const [metrics] = useState({
    activeConversations: 0,
    emailsSent: 0,
    avgResponseTime: 0,
    applicationsSubmitted: 0,
    viewingsScheduled: 0,
    successRate: 0
  });

  const metricCards = [
    {
      title: "Active Conversations",
      value: metrics.activeConversations,
      icon: MessageSquare,
      color: "text-primary",
      bgColor: "bg-primary/10"
    },
    {
      title: "Emails Sent Today",
      value: metrics.emailsSent,
      icon: Mail,
      color: "text-accent",
      bgColor: "bg-accent/10"
    },
    {
      title: "Avg Response Time",
      value: `${metrics.avgResponseTime.toFixed(1)}h`,
      icon: TrendingUp,
      color: "text-success",
      bgColor: "bg-success/10"
    },
    {
      title: "Applications Submitted",
      value: metrics.applicationsSubmitted,
      icon: CheckCircle,
      color: "text-warning",
      bgColor: "bg-warning/10"
    },
    {
      title: "Viewings Scheduled",
      value: metrics.viewingsScheduled,
      icon: Calendar,
      color: "text-primary",
      bgColor: "bg-primary/10"
    },
    {
      title: "Success Rate",
      value: `${metrics.successRate.toFixed(0)}%`,
      icon: Target,
      color: "text-success",
      bgColor: "bg-success/10"
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {metricCards.map((metric, index) => {
        const Icon = metric.icon;
        return (
          <Card key={index} className="transition-all hover:shadow-md">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">
                    {metric.title}
                  </p>
                  <p className="text-2xl font-bold bounce-in">
                    {metric.value}
                  </p>
                </div>
                <div className={`p-3 rounded-full ${metric.bgColor}`}>
                  <Icon className={`w-6 h-6 ${metric.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};