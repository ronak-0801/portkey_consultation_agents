import os
import requests
from typing import Optional, Union, List, Dict
from datetime import datetime

def send_slack_message(message: str = "", blocks: List[Dict] = None, channel: str = "#social") -> Optional[dict]:
    """
    Send a message to Slack channel using either simple text or blocks
    
    Args:
        message (str): Simple text message to send (optional)
        blocks (List[Dict]): Slack blocks for formatted message (optional)
        channel (str): Slack channel to send message to
    
    Returns:
        dict: Slack API response or None if failed
    """
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    
    if not slack_token:
        print("Error: SLACK_BOT_TOKEN environment variable not set")
        return None
        
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    data = {
        "channel": channel,
    }
    
    # Add either blocks or text to the payload
    if blocks:
        data["blocks"] = blocks
    if message:
        data["text"] = message
    
    try:
        response = requests.post(
            "https://slack.com/api/chat.postMessage", 
            headers=headers, 
            json=data
        )
        return response.json()
    except Exception as e:
        print(f"Error sending message to Slack: {e}")
        return None 