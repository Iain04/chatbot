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
function_assistant_messages = []
assistant_messages = []
url_official = "https://changiairport.crowneplaza.com/day-use-room"
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
                    "description": "The users check in date of the hotel room. The format must be Y-m-d.",
                },
                "check_out_date": {
                    "type": "string",
                    "format": "date",
                    "description": "The users check out date of the hotel room. The format must be Y-m-d.",
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
]

def generate_chat_response(message_hist):
    try:
        # Append messages from message_hist to messages
        messages.extend(message_hist)

        chat_response = chat_completion_request(
            messages, functions=functions
        )

        assistant_response = chat_response.json()["choices"][0]["message"]
        assistant_message = assistant_response["content"]
        assistant_messages.append(assistant_message)
        print(chat_response.json())

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

                rooms_data, url, check_values, data_dict = webscrap.scape_hotel(num_adult, num_children, num_rooms, check_in_date, check_out_date)

                # Check if there is rooms retrieved is None or Url is None
                if url is None or data_dict is None or check_values is None:
                    function_assistant_messages.append("Sorry I am unable to answer your question right now. Try again later.")
                else:
                    # Check if there are any invalid inputs
                    if check_values == True:
                        function_assistant_messages.append("Apologies, some of your inputs were invalid.")
                    
                    loop_message = ""

                    # Format and print the extracted room information in chatbot style
                    function_assistant_messages.append(f"Here are the available rooms for, Date: {data_dict['date_range']}, Guests: {data_dict['guest_count']}, Rooms: {data_dict['room_count']}.")

                    # Loop to display the rooms info
                    if rooms_data is None:
                        function_assistant_messages.append("We do not have any rooms matching your criteria.")
                        function_assistant_messages.append(f"<a href='{url_official}' target='_blank'>Click here</a>, if you would like to check the website out yourself!")
                    else:
                        for idx, room in enumerate(rooms_data, start=1):
                            room_name = room["name"]
                            room_price = room["price"]

                            room_message = f"(Room {idx}: Name: {room_name} Price: {room_price})"
                            loop_message += room_message
                    
                        function_assistant_messages.append(loop_message)
                        function_assistant_messages.append(f"If you would like to book any one of the rooms, <a href='{url}' target='_blank'>Click here to book</a>.")
                return function_assistant_messages

        return assistant_messages
    
    except KeyError as e:
        # Print the full response JSON to see the error details
        print(chat_response.json())
        return None

