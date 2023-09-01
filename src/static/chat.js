// Constant variables
const roomName = localStorage.getItem('roomName'); // Room name

// Function to create messages
function message_load(message, time, user) {
    // Get the template element based on user 
    if (user === 'user') {
        var messageTemplate = document.getElementById('message-template-user');
    } else {
        var messageTemplate = document.getElementById('message-template-chatbot');
    }
    // Clone the template
    var newMessage = messageTemplate.cloneNode(true);
    newMessage.style.display = ''; // Show the cloned template
    newMessage.innerHTML = newMessage.innerHTML
        .replace("MESSAGE_CONTENT", message)
        .replace("TIME", time);
    // Append the new message to the chat container
    const chatContainer = document.querySelector('#chat-container');
    chatContainer.appendChild(newMessage);
}

// Function to store messages in local storage
function message_store(message, time, user) {
    // Create a new message object with role, content, timestamp
    const newMessage = {
        role: user,
        content: message,
        timestamp: time
    };

    var existingMessages = JSON.parse(localStorage.getItem('chatMessages')) || [];
    // Add the new message to the existingMessages array
    existingMessages.push(newMessage);

    // Store the updated messages array back in local storage
    localStorage.setItem('chatMessages', JSON.stringify(existingMessages));
}

// Establish chatsocket connection
const chatSocket = new ReconnectingWebSocket(
    'ws://'
    + window.location.host
    + '/ws/chat/'
    + roomName
    + '/'
);

// Chatsocket functions

chatSocket.onopen = function(e) {
    var existingMessages = JSON.parse(localStorage.getItem('chatMessages')) || [];

    // Render existing messages in the chat interface
    existingMessages.forEach(message => {
        message_load(message.content, message.timestamp, message.role)
    });
}

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log(data)

    var message = data['message']
    var assistant_message = data['assistant_message']

    // Handler for user messages
    // Check if the message is empty
    if (message === '') {
        console.log("Message is empty");
        return; // End the function
    }
    // Get current time
    var currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    
    if ('message' in data) {
        message_load(message, currentTime, 'user'); // Show messages in html
        message_store(message, currentTime, 'user'); // Store in local storage
    }
    
    // Handler for assistant messages
    if ('assistant_message' in data) {
        message_load(assistant_message, currentTime, 'assistant'); // Show messages in html
        message_store(assistant_message, currentTime, 'assistant'); // Store in local storage
    }    

    // Scroll chat to the bottom
    var scroll_container = document.getElementById("scroll-container");
    scroll_container.scrollTop = scroll_container.scrollHeight;
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};
document.querySelector('#chat-message-input').focus();
document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.keyCode === 13) {  // enter, return
        document.querySelector('#chat-message-submit').click();
    }
};

document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    const existingMessages = JSON.parse(localStorage.getItem('chatMessages'));
    console.log(existingMessages)
    console.log(message)

    // Handle new message and existing messages
    chatSocket.send(JSON.stringify({
        'command': 'send_all_messages',
        'message_new': message,
        'messages': existingMessages,
    }));
    messageInputDom.value = '';
};