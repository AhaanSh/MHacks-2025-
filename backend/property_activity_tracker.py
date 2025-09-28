import json
import os
from datetime import datetime
from typing import Dict, List, Any

class PropertyActivityTracker:
    """Track property-related message activities for the recent activity feed"""
    
    def __init__(self, storage_file: str = "property_activities.json"):
        self.storage_file = storage_file
        self.activities = self._load_activities()
    
    def _load_activities(self) -> List[Dict[str, Any]]:
        """Load existing activities from storage"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_activities(self):
        """Save activities to storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.activities, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving activities: {e}")
    
    def log_message_sent(self, 
                        recipient_email: str,
                        subject: str,
                        message_id: str = None) -> str:
        """
        Log when a message is sent to a realtor
        
        Args:
            recipient_email: Email of the recipient
            subject: Subject of the email
            message_id: AgentMail message ID
        
        Returns:
            Activity ID
        """
        activity_id = f"msg_{len(self.activities) + 1}_{int(datetime.now().timestamp())}"
        
        # Extract property info from subject if available
        property_info = subject if subject else "Property inquiry"
        
        activity = {
            "id": activity_id,
            "type": "message_sent",
            "recipient_email": recipient_email,
            "subject": subject,
            "property_info": property_info,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat(),
            "time": datetime.now().strftime("%I:%M %p"),
            "icon": "📧",
            "text": f"Contacted {recipient_email.split('@')[0]} about {property_info}"
        }
        
        self.activities.insert(0, activity)  # Add to beginning for latest first
        
        # Keep only last 100 activities to prevent file from growing too large
        if len(self.activities) > 100:
            self.activities = self.activities[:100]
        
        self._save_activities()
        return activity_id
    
    def get_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activities with limit"""
        return self.activities[:limit]
    
    def get_property_activities(self, property_address: str) -> List[Dict[str, Any]]:
        """Get all activities for a specific property"""
        return [
            activity for activity in self.activities 
            if activity.get('property_address') == property_address
        ]
    
    def get_property_message_logs(self, property_address: str) -> List[Dict[str, Any]]:
        """Get message logs for a specific property"""
        property_activities = self.get_property_activities(property_address)
        
        message_logs = []
        for activity in property_activities:
            if activity.get('type') == 'property_message':
                message_logs.append({
                    'id': activity['id'],
                    'sender': 'ai' if activity['message_type'] == 'sent' else activity['recipient_email'],
                    'recipient': activity['recipient_email'] if activity['message_type'] == 'sent' else 'ai',
                    'content': activity['message_content'],
                    'timestamp': activity['timestamp'],
                    'message_id': activity.get('message_id'),
                    'thread_id': activity.get('thread_id')
                })
        
        return sorted(message_logs, key=lambda x: x['timestamp'])
    
    def create_property_card_data(self) -> List[Dict[str, Any]]:
        """Create property card data for recent activity UI"""
        property_cards = {}
        
        for activity in self.activities:
            if activity.get('type') == 'property_message':
                address = activity['property_address']
                
                if address not in property_cards:
                    property_cards[address] = {
                        'property_address': address,
                        'last_activity': activity['timestamp'],
                        'message_count': 0,
                        'latest_message': activity['message_content'],
                        'contact_email': activity['recipient_email'],
                        'activity_id': activity['id']
                    }
                
                property_cards[address]['message_count'] += 1
        
        # Convert to list and sort by last activity
        cards = list(property_cards.values())
        cards.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return cards[:10]  # Return top 10 most recent