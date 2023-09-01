import json
from . import openai_utils as oau
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json.get("command")
        
        if command == "send_all_messages":
            # Local storage messages
            existing_messages = text_data_json["messages"]
            # New message
            new_message = text_data_json["message_new"]
            # Remove 'timestamp' key from each dictionary
            if existing_messages:  # Check if the list is not empty
                for message in existing_messages:
                    if 'timestamp' in message:
                        del message['timestamp']

            # Convert existing_messages to a list if it's None
            if existing_messages is None:
                existing_messages = []

            existing_messages.append({"role": "user", "content": new_message})


            # Send new message instantly back
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat_message", "message": new_message}
            )
            
            # Use chatgpt to generate a response
            assistant_messages = oau.generate_chat_response(existing_messages)

            if assistant_messages == None:  # Check if there is an error
                await self.channel_layer.group_send(
                    self.room_group_name, {"type": "bot_message", "assistant_message": "Sorry for the inconvenience, I am unable to answer your question right now. Try again later."}
                )
            else:
                for assistant_message in assistant_messages:
                    await self.channel_layer.group_send(
                        self.room_group_name, {"type": "bot_message", "assistant_message": assistant_message}
                    )


    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    # Receive assistant message from chatgpt
    async def bot_message(self, event):
        assistant_message = event["assistant_message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"assistant_message": assistant_message}))