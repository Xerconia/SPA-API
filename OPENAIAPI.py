import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(env_path)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAIKEY2"])
assistantID = os.environ["ASSISTANTID"]

def create_thread():
    """
    Create a new thread using the OpenAI API and return its ID.
    """
    thread = client.beta.threads.create()
    threadID = thread.id
    return threadID

def messageOpenAI(message: str, threadID: str):
    """
    Send a message to the OpenAI API and wait for the response.

    Args:
        message (str): The message to send.
        threadID (str): The ID of the thread to use.

    Returns:
        str: The text value of the last message from the OpenAI API.
    """
    # Create a new message in the thread
    client.beta.threads.messages.create(
        thread_id=threadID,
        role="user",
        content=message
    )

    # Start a new run in the thread
    run = client.beta.threads.runs.create(
        thread_id=threadID,
        assistant_id=assistantID,
    )

    while True:
        try:
            # Retrieve the run
            run = client.beta.threads.runs.retrieve(thread_id=threadID, run_id=run.id)

            # If the run is completed, print the elapsed time and return the last message
            if run.completed_at:
                elapsedTime = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime("%H:%M:%S:", time.gmtime(elapsedTime))
                print(f"Run completed in {formatted_elapsed_time}")

                messages = client.beta.threads.messages.list(thread_id=threadID)
                last_message = messages.data[0]
                return last_message.content[0].text.value
        except Exception as e:
            return "Error has occured"

        # Log a message and sleep for 5 seconds before checking again
        logging.info("Waiting for run to complete...")
        time.sleep(5)
