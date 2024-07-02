import os
from pathlib import Path
from dotenv import load_dotenv
from threading import Lock, Thread
import datetime
import time
from flask import Flask
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from http.client import responses
from slackeventsapi import SlackEventAdapter
import OPENAIAPI

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(env_path)

# Initialize Flask app and Slack client
app = Flask(__name__)
wclient = WebClient(token=os.environ['BOTTOKEN'])

# Initialize SocketModeClient with an app-level token + WebClient
socket_mode_client = SocketModeClient(app_token=os.environ['SLACKTOKEN'], web_client=wclient)
botID = wclient.api_call("auth.test")["user_id"]

# Dictionary to store thread IDs for each user
user_threads = {}

# Create a lock
lock = Lock()

# Process incoming requests from Slack
@socket_mode_client.socket_mode_request_listeners.append
def process(client: SocketModeClient, req: SocketModeRequest):
    
    # Gather the Slack Events
    if req.type == "events_api":
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)
        
        #Look specifically for incoming direct message
        if req.payload["event"]["type"] == "message" \
            and req.payload["event"].get("subtype") is None \
            and req.payload["event"]["channel"].startswith('D'):
            channel_id = req.payload["event"]["channel"]
            user_id = req.payload["event"]["user"]
            text = req.payload["event"]["text"]
            
            #Deal with race condition for key value pairs, Note: Flask is single threaded.
            with lock:
                if user_id in user_threads:
                    threadID = user_threads[user_id]
                else:
                    threadID = OPENAIAPI.create_thread()
                    user_threads[user_id] = threadID
                    
            # Send back the same message to the user
            if botID != user_id:
                response = OPENAIAPI.messageOpenAI(text,threadID)
                wclient.chat_postMessage(channel=channel_id, text=response)
         
# Function to clear the dictionary every day at midnight
def clear_user_threads():
    while True:
        # Calculate the time until the next midnight
        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        sleep_time = (midnight - now).total_seconds()

        # Sleep until midnight
        time.sleep(sleep_time)

        # Clear the dictionary
        user_threads.clear()
        
# Function to start the Socket Mode client and handle disconnects
def start_socket_mode_client():
    while True:
        if not socket_mode_client.is_connected():
            try:
                socket_mode_client.connect()
                print("Socket Mode Connected")
            except Exception as e:
                print(f"Error connecting to Slack: {e}")
                print("Reconnecting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    
    # Start the background thread
    Thread(target=clear_user_threads).start()
    Thread(target=start_socket_mode_client).start()
    app.run(debug=True)
