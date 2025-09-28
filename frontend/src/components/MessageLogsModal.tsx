import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Mail, MessageCircle, X, Clock } from "lucide-react";

interface MessageLog {
  id: string;
  sender: string;
  recipient: string;
  content: string;
  timestamp: string;
  message_id?: string;
  type: 'sent' | 'received';
}

interface MessageLogsModalProps {
  isOpen: boolean;
  onClose: () => void;
  propertyInfo: string;
  recipientEmail: string;
}

export const MessageLogsModal = ({ isOpen, onClose, propertyInfo, recipientEmail }: MessageLogsModalProps) => {
  // Mock message logs - in production this would come from your backend API
  const [messageLogs] = useState<MessageLog[]>([
    {
      id: "1",
      sender: "ai",
      recipient: recipientEmail,
      content: `Hello! This is rentAI, your AI rental assistant.\n\nThank you for reaching out to rental@agentmail.to. I'm interested in learning more about the ${propertyInfo}.\n\nI'm here to help you find the perfect rental property. I can assist you with:\n- Property searches based on your budget and preferences\n- Location-based recommendations\n- Bedroom and bathroom requirements\n- Property type preferences (apartment, house, condo, etc.)\n\nPlease reply with more details about this property!\n\nBest regards,\nrentAI`,
      timestamp: new Date().toISOString(),
      type: 'sent'
    }
  ]);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader className="flex flex-row items-center justify-between">
          <div className="flex-1">
            <DialogTitle className="text-xl font-semibold flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-primary" />
              Message Logs
            </DialogTitle>
            <div className="mt-2 space-y-1">
              <p className="text-sm text-muted-foreground">
                📍 <span className="font-medium">{propertyInfo}</span>
              </p>
              <p className="text-sm text-muted-foreground">
                📧 <span className="font-medium">{recipientEmail}</span>
              </p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="h-6 w-6 p-0"
          >
            <X className="w-4 h-4" />
          </Button>
        </DialogHeader>

        <ScrollArea className="max-h-[500px] pr-4">
          <div className="space-y-4">
            {messageLogs.length > 0 ? (
              messageLogs.map((log) => (
                <div
                  key={log.id}
                  className={`p-4 rounded-lg border ${
                    log.type === 'sent' 
                      ? 'bg-primary/5 border-primary/20 ml-8' 
                      : 'bg-muted/50 border-muted mr-8'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant={log.type === 'sent' ? 'default' : 'secondary'}
                        className={log.type === 'sent' ? 'bg-primary text-primary-foreground' : ''}
                      >
                        {log.type === 'sent' ? (
                          <>
                            <Mail className="w-3 h-3 mr-1" />
                            Sent
                          </>
                        ) : (
                          <>
                            <MessageCircle className="w-3 h-3 mr-1" />
                            Received
                          </>
                        )}
                      </Badge>
                      <span className="text-sm font-medium">
                        {log.type === 'sent' ? '🤖 rentAI' : `👤 ${log.sender}`}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {formatTime(log.timestamp)}
                    </div>
                  </div>
                  
                  <div className="text-sm text-foreground whitespace-pre-wrap">
                    {log.content}
                  </div>
                  
                  {log.message_id && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      Message ID: {log.message_id}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <MessageCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Messages Yet</h3>
                <p className="text-muted-foreground text-sm">
                  Message logs will appear here once communication begins.
                </p>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="flex justify-between items-center pt-4 border-t">
          <div className="text-sm text-muted-foreground">
            {messageLogs.length} message{messageLogs.length !== 1 ? 's' : ''} total
          </div>
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};