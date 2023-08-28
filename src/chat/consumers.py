import json
from . import openai_utils as oau

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class ChatConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json.get("command")

        if command == "new_message":
            # Handle new message
            message = text_data_json["message"]
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "chat_message", "message": message}
            )
        
        elif command == "send_existing_messages":
            # Handle incoming local storage messages
            existing_messages = text_data_json["messages"]
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
            # Use chatgpt to generate a response
            assistant_message = oau.generate_chat_response(existing_messages)

            if assistant_message == None: # Check if there is an error
                return
            
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "bot_message", "assistant_message": assistant_message}
            )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))

    # Receive assistant message from chatgpt
    def bot_message(self, event):
        assistant_message = event["assistant_message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"assistant_message": assistant_message}))