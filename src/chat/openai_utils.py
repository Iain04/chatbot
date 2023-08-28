import os

import openai
from datetime import datetime
import json
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
from dotenv import load_dotenv

from . import webscraping as webscrap

# Load environment variables from .env file
load_dotenv()

# Use API Key and set the GPT model
openai.api_key = os.environ.get('OPENAI_API_KEY')
GPT_MODEL = "gpt-3.5-turbo-0613"

# Global variable
messages = []
# Appending the system information of the bot
messages.append({"role": "system", 
                 "content": """You are a laconic assistant for Crowne Plaza Hotel Singapore. 
                 You reply with brief, to-the-point answers with no elaboration.
                 You only reply if the topic is regarding Crowne Plaza Hotel Singapore. 
                 You refuse to reply if the topic is not about Crowne Plaza Hotel Singapore."""
                })

"You are a laconic assistant. You reply with brief, to-the-point answers with no elaboration."
messages.append({'role': 'assistant', 'content': 'Hello, welcome to Crowne Plaza Chatbot. How can I help you today?'})

# Function to make a Chat Completetion request
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, functions=None, function_call=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + openai.api_key,
    }
    json_data = {"model": model, "messages": messages}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

# Functions for Chat Completions API to generate specific responses
functions = [
    {
        "name": "get_hotel_availability",
        "description": "Get the hotel room availability. Ask for confirmation displaying each property",
        "parameters": {
            "type": "object",
            "properties": {
                "check_in_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The users check in date of the hotel room.",
                },
                "check_out_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The users check out date of the hotel room.",
                },
                "num_adult": {
                    "type": "integer",
                    "description": "The number of adults for the hotel room.",
                },
                "num_children": {
                    "type": "integer",
                    "description": "The number of children for the hotel room. If the user did not state the number of children assume the value to be 0",
                },
                "num_rooms": {
                    "type": "integer",
                    "description": "The number of rooms needed for the user. If the user did not state the number of rooms make the value 1",
                },
            },
            "required": ["check_in_date", "check_out_date", "num_adult", "num_children", "num_rooms"],
        },
    },
    {
        "name": "get_n_day_weather_forecast",
        "description": "Get an N-day weather forecast",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "format": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the users location.",
                },
                "num_days": {
                    "type": "integer",
                    "description": "The number of days to forecast",
                }
            },
            "required": ["location", "format", "num_days"]
        },
    },
]

def generate_chat_response(message_hist):
    try:
        # Append messages from message_hist to messages
        messages.extend(message_hist)

        chat_response = chat_completion_request(
            messages, functions=functions
        )

        print(chat_response.json())

        assistant_response = chat_response.json()["choices"][0]["message"]
        assistant_message = assistant_response["content"]

        # Check if there is a function_call
        if chat_response.json()["choices"][0]["finish_reason"] == "function_call":
            # Check for the function get_hotel_availability
            if assistant_response["function_call"]["name"] == "get_hotel_availability":
                arguments = json.loads(assistant_response["function_call"]["arguments"])

                # Declare Each function variable
                check_in_date = arguments["check_in_date"]
                check_out_date = arguments["check_out_date"]
                num_adult = arguments["num_adult"]
                num_children = arguments["num_children"]
                num_rooms = arguments["num_rooms"]

                rooms_data = webscrap.scape_hotel(num_adult, num_children, num_rooms, check_in_date, check_out_date)
                # Format and print the extracted room information in chatbot style
                function_rooms_message = "Here are the available rooms:\n\n"
                for idx, room in enumerate(rooms_data, start=1):
                    room_name = room["name"]
                    room_price = room["price"]

                    room_message = f"Room {idx}:\nName: {room_name}\nPrice: {room_price}\n\n"
                    function_rooms_message += room_message

                return function_rooms_message


        return assistant_message
    
    except KeyError as e:
        # Print the full response JSON to see the error details
        print(chat_response.json())
        return None


    