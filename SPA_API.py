from http.client import responses
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slackeventsapi import SlackEventAdapter
from OPENAIAPI import messageOpenAI

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(env_path)

# Initialize Flask app and Slack client
app = Flask(__name__)
wclient = WebClient(token=os.environ['TARPBOT'])

# Initialize SocketModeClient with an app-level token + WebClient
socket_mode_client = SocketModeClient(app_token=os.environ['TARPTOKEN'], web_client=wclient)
botID = wclient.api_call("auth.test")["user_id"]

# Process incoming requests from Slack
@socket_mode_client.socket_mode_request_listeners.append
def process(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)
        if req.payload["event"]["type"] == "message" \
            and req.payload["event"].get("subtype") is None \
            and req.payload["event"]["channel"].startswith('D'):
            channel_id = req.payload["event"]["channel"]
            user_id = req.payload["event"]["user"]
            text = req.payload["event"]["text"]
            # Send back the same message to the user
            if botID != user_id:
                response = messageOpenAI(text)
                wclient.chat_postMessage(channel=channel_id, text=response)
                
if __name__ == "__main__":
    socket_mode_client.connect()
    app.run(debug=True)
