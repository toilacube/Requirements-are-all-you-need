from fastapi import FastAPI
from src.agent import LangGraphChatbot, ChatRequest, ChatResponse, ChatStreamRequest
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# FastAPI application
app = FastAPI(title="LangGraph Chatbot API")

# Allow all cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the chatbot
chatbot = LangGraphChatbot()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Async Chat endpoint that processes user messages and returns bot responses.
    """
    return await chatbot.chat(request)


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatStreamRequest):
    """
    Streaming chat endpoint that returns Server-Sent Events (SSE).
    
    Stream modes:
    - "messages": Stream LLM tokens as they're generated
    - "updates": Stream node execution updates
    - "values": Stream full state after each node
    """
    return StreamingResponse(
        chatbot.stream_chat(request),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.post("/chat/sync", response_model=ChatResponse)
def chat_sync_endpoint(request: ChatRequest):
    """
    Synchronous chat endpoint for simpler use cases.
    """
    return chatbot.chat_sync(request)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

    """Serve a simple demo page for testing the streaming chat."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LangGraph Streaming Chat Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            #chat-container { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; margin: 20px 0; }
            #message-input { width: 70%; padding: 10px; }
            #send-button { padding: 10px 20px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background-color: #e3f2fd; text-align: right; }
            .assistant { background-color: #f3e5f5; }
            .streaming { background-color: #fff3e0; }
            select { padding: 5px; margin: 10px; }
        </style>
    </head>
    <body>
        <h1>LangGraph Streaming Chat Demo</h1>
        
        <div>
            <label>Stream Mode: 
                <select id="stream-mode">
                    <option value="messages">Messages (LLM Tokens)</option>
                    <option value="updates">Updates (Node Progress)</option>
                    <option value="values">Values (Full State)</option>
                </select>
            </label>
        </div>
        
        <div id="chat-container"></div>
        
        <div>
            <input type="text" id="message-input" placeholder="Type your message..." />
            <button id="send-button">Send</button>
        </div>

        <script>
            const chatContainer = document.getElementById('chat-container');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            const streamModeSelect = document.getElementById('stream-mode');

            let conversationHistory = [];

            function addMessage(content, type) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.textContent = content;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                return messageDiv;
            }

            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;

                // Add user message to chat
                addMessage(message, 'user');
                conversationHistory.push({role: 'user', content: message});

                // Clear input
                messageInput.value = '';
                sendButton.disabled = true;

                // Create streaming message container
                const streamingDiv = addMessage('', 'streaming');
                let currentResponse = '';

                try {
                    const response = await fetch('/chat/stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            conversation_history: conversationHistory,
                            stream_mode: streamModeSelect.value
                        }),
                    });

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    
                                    if (data.type === 'token') {
                                        currentResponse += data.content;
                                        streamingDiv.textContent = currentResponse;
                                    } else if (data.type === 'update' || data.type === 'values') {
                                        streamingDiv.textContent = JSON.stringify(data.content, null, 2);
                                    } else if (data.type === 'done') {
                                        // Convert streaming div to assistant message
                                        streamingDiv.className = 'message assistant';
                                        if (streamModeSelect.value === 'messages') {
                                            conversationHistory.push({role: 'assistant', content: currentResponse});
                                        }
                                    } else if (data.type === 'error') {
                                        streamingDiv.textContent = `Error: ${data.content}`;
                                        streamingDiv.style.backgroundColor = '#ffebee';
                                    }
                                } catch (e) {
                                    console.error('Failed to parse SSE data:', e);
                                }
                            }
                        }
                    }
                } catch (error) {
                    streamingDiv.textContent = `Error: ${error.message}`;
                    streamingDiv.style.backgroundColor = '#ffebee';
                } finally {
                    sendButton.disabled = false;
                }
            }

            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    """
# Example usage
if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
