from concurrent.futures import thread
import os
from pathlib import Path
from urllib import response
from dotenv import load_dotenv
import time
import logging
from datetime import datetime

from openai import OpenAI
import openai

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(env_path)

client = openai.OpenAI(api_key=os.environ["OPENAIKEY2"])
assistantID = os.environ["ASSISTANTID"]

def messageOpenAI(message: str):
    thread = client.beta.threads.create()
    threadID = thread.id
    message = client.beta.threads.messages.create(
        thread_id=threadID,
        role="user",
        content=message
        )
    
    run = client.beta.threads.runs.create(
        thread_id=threadID,
        assistant_id=assistantID,
        )
    
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=threadID,run_id=run.id)
            if run.completed_at:
                elapsedTime = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime("%H:%M:%S:", time.gmtime(elapsedTime))
                print(f"Run completed in {formatted_elapsed_time}")
                messages = client.beta.threads.messages.list(thread_id=threadID)
                last_message = messages.data[0]
                return last_message.content[0].text.value
        except Exception as e:
            return "Error has occured"
        logging.info("Waiting for run to complete...")
        time.sleep(5)

