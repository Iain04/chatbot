import os

import openai
from datetime import datetime
import json
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI

from langchain.tools import BaseTool
from typing import Optional, Type
from langchain.agents import initialize_agent, Tool, AgentType
from pydantic import BaseModel, Field
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.schema import messages_from_dict, messages_to_dict

from pathlib import Path
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA

from . import webscraping as webscrap

# Load environment variables from .env file
load_dotenv()

# Use API Key and set the GPT model
openai_api_key = os.environ.get('OPENAI_API_KEY')
GPT_MODEL = "gpt-3.5-turbo-0613"

# Global variable
messages = []
function_assistant_messages = []
assistant_messages = []
url_official = "https://changiairport.crowneplaza.com/day-use-room"

llm = ChatOpenAI(openai_api_key=openai_api_key, model=GPT_MODEL, temperature=0,)


# Create tools

# Custom tool for getting hotel room avalibility
class CheckRoomCheckInput(BaseModel):
    """Input for Hotel room avaliblity."""

    num_adult: int = Field(..., description="The number of adults for the hotel room.")
    num_children: int = Field(..., description="The number of children for the hotel room. If the user did not state the number of children assume the value to be 0.")
    num_rooms: int = Field(..., description="The number of rooms needed for the user. If the user did not state the number of rooms make the value 1.")
    check_in_date: str = Field(..., description="The users check in date of the hotel room. The format must be d-m-Y.")
    check_out_date: str = Field(..., description="The users check out date of the hotel room. The format must be d-m-Y.")

class CheckRoomTool(BaseTool):
    name = "get_hotel_availability"
    description = "Gets the hotel room availability."

    def _run(self, num_adult: int, num_children: int, num_rooms: int, check_in_date: str, check_out_date: str):
        # print("i'm running")
        rooms = webscrap.scape_hotel(num_adult, num_children, num_rooms, check_in_date, check_out_date)

        #  url_html = f"<a href='{new_url}' target='_blank'>Click here</a>"

        return rooms #, url_html, data_dict

    def _arun(self, num_adult: int, num_children: int, num_rooms: int, check_in_date: str, check_out_date: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = CheckRoomCheckInput

# Tool for Crowne Plaza matters
doc_path = str(Path("C:/Users/iainl/OneDrive/Documents/Year3/MP/Project/src/chat/data.txt"))
loader = TextLoader(doc_path)
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
docsearch = Chroma.from_documents(texts, embeddings, collection_name="data")

search_doc = RetrievalQA.from_chain_type(
    llm=llm, chain_type="stuff", retriever=docsearch.as_retriever()
)

tools = [CheckRoomTool(),
        Tool(
            name="get_doc_info",
            func=search_doc.run,
            description="A document search. Use this only if you cannot answer the question and require more information.",
        ),]

agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="chat_history")],
}
system_message = SystemMessage(
                    content='''You are a laconic assistant for Crowne Plaza Hotel Singapore. 
                    You reply with brief, to-the-point answers with no elaboration.
                    You only reply if the topic is regarding Crowne Plaza Hotel Singapore. 
                    You refuse to reply if the topic is not about Crowne Plaza Hotel Singapore.
                    '''
                )

def generate_chat_response(message_hist):
    try:
        # Retrieve new message
        new_message_dict = message_hist[-1]  # Retrieve the last dictionary in the list
        new_message = new_message_dict.get("content")
        # transform data
        # Define a mapping from "role" to "type"
        role_to_type = {"user": "human", "assistant": "ai"}
        transformed_data = [
            {
                'type': role_to_type[entry['role']],
                'data': {
                    'content': entry['content'],
                    'additional_kwargs': {}
                }
            }
            for entry in message_hist
        ]
        
        transformed_data = transformed_data[:-1] # Remove newest message from the message_obj

        message_obj = messages_from_dict(transformed_data)
        chat_memory = ChatMessageHistory(chat_memory=message_obj)
        if len(transformed_data) > 1:
            memory = ConversationBufferMemory(chat_memory=chat_memory, memory_key="chat_history", return_messages=True)
            print("1")
        else:
             memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
             print("2")

        open_ai_agent = initialize_agent(tools,
                            llm,
                            agent=AgentType.OPENAI_FUNCTIONS,
                            memory=memory,
                            verbose=True,
                            agent_kwargs={
                            "system_message": system_message,
                            "memory": memory
                        })
        
        response = open_ai_agent.run(new_message)
        return response

    except Exception as e:
        print(e)
        return None



# def generate_chat_response(message_hist):
#     try:
#         # Append messages from message_hist to messages
#         messages.extend(message_hist)

#         chat_response = chat_completion_request(
#             messages, functions=functions
#         )

#         assistant_response = chat_response.json()["choices"][0]["message"]
#         assistant_message = assistant_response["content"]
#         assistant_messages.append(assistant_message)
#         print(chat_response.json())

#         # Check if there is a function_call
#         if chat_response.json()["choices"][0]["finish_reason"] == "function_call":
#             # Check for the function get_hotel_availability
#             if assistant_response["function_call"]["name"] == "get_hotel_availability":
#                 arguments = json.loads(assistant_response["function_call"]["arguments"])

#                 # Declare Each function variable
#                 check_in_date = arguments["check_in_date"]
#                 check_out_date = arguments["check_out_date"]
#                 num_adult = arguments["num_adult"]
#                 num_children = arguments["num_children"]
#                 num_rooms = arguments["num_rooms"]

#                 rooms_data, url, data_dict = webscrap.scape_hotel(num_adult, num_children, num_rooms, check_in_date, check_out_date)

#                 # Check if there is rooms retrieved is None or Url is None
#                 if url is None or data_dict is None:
#                     function_assistant_messages.append("Sorry I am unable to answer your question right now. Try again later.")
#                 else:
                    
#                     loop_message = ""

#                     # Format and print the extracted room information in chatbot style
#                     function_assistant_messages.append(f"Here are the available rooms for, Date: {data_dict['date_range']}, Guests: {data_dict['guest_count']}, Rooms: {data_dict['room_count']}.")

#                     # Loop to display the rooms info
#                     if rooms_data is None:
#                         function_assistant_messages.append("We do not have any rooms matching your criteria.")
#                         function_assistant_messages.append(f"<a href='{url_official}' target='_blank'>Click here</a>, if you would like to check the website out yourself!")
#                     else:
#                         for idx, room in enumerate(rooms_data, start=1):
#                             room_name = room["name"]
#                             room_price = room["price"]

#                             room_message = f"(Room {idx}: Name: {room_name} Price: {room_price})"
#                             loop_message += room_message
                    
#                         function_assistant_messages.append(loop_message)
#                         function_assistant_messages.append(f"If you would like to book any one of the rooms, <a href='{url}' target='_blank'>Click here to book</a>.")
#                 return function_assistant_messages

#         return assistant_messages
    
#     except KeyError as e:
#         # Print the full response JSON to see the error details
#         print(chat_response.json())
#         return None

