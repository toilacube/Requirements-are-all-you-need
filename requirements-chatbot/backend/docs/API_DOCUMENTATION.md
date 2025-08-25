# Chatbot API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Streaming Chat (Recommended for Frontend)

**Endpoint:** `POST /chat/stream`

**Description:** Real-time streaming chat endpoint that returns Server-Sent Events (SSE) for live token streaming.

#### Request Body
```json
{
  "message": "string",
  "conversation_history": [
    {
      "role": "user|assistant",
      "content": "string"
    }
  ],
  "stream_mode": "messages"
}
```

#### Request Parameters
- `message` (string, required): The user's message
- `conversation_history` (array, optional): Previous conversation messages
- `stream_mode` (string, optional): Stream mode - defaults to "messages"
  - `"messages"`: Stream LLM tokens as they're generated
  - `"updates"`: Stream node execution updates
  - `"values"`: Stream full state after each node

#### Response
Server-Sent Events (SSE) stream with the following event types:

**Token Events:**
```
data: {"type": "token", "content": "I"}
data: {"type": "token", "content": " am doing well"}
data: {"type": "token", "content": ", thank you for asking!"}
```

**Completion Event:**
```
data: {"type": "done"}
```

#### Headers
- `Content-Type: application/json`
- `Accept: text/event-stream`

#### Example cURL
```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "conversation_history": []
  }'
```

#### Frontend Implementation Example (JavaScript)
```javascript
async function streamChat(message, conversationHistory = []) {
  const response = await fetch('http://localhost:8000/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      conversation_history: conversationHistory,
      stream_mode: 'messages'
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.type === 'token') {
          // Append token to UI
          appendTokenToChat(data.content);
        } else if (data.type === 'done') {
          // Stream complete
          onStreamComplete();
        }
      }
    }
  }
}
```


## Data Models

### ChatMessage
```typescript
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
```

### ChatRequest
```typescript
interface ChatRequest {
  message: string;
  conversation_history?: ChatMessage[];
}
```

### ChatStreamRequest
```typescript
interface ChatStreamRequest {
  message: string;
  conversation_history?: ChatMessage[];
  stream_mode?: "messages" | "updates" | "values" | "custom";
}
```

### ChatResponse
```typescript
interface ChatResponse {
  response: string;
  conversation_history: ChatMessage[];
}
```

---

## Frontend Implementation Guidelines

### 1. Recommended Approach: Use Streaming Endpoint

The `/chat/stream` endpoint provides the best user experience with real-time token streaming.

### 2. Conversation Management

- Maintain conversation history in frontend state
- Include previous messages in each request for context
- Update conversation history after each exchange

### 3. Error Handling

```javascript
try {
  // API call
} catch (error) {
  console.error('Chat API error:', error);
  // Show user-friendly error message
}
```

### 4. CORS Headers

The API includes CORS headers for cross-origin requests:
- `Access-Control-Allow-Origin: *`

### 5. Connection Management

For streaming:
- Handle connection drops gracefully
- Implement retry logic for failed streams
- Close connections properly when component unmounts

---

## Example Frontend Integration

### React Hook Example
```javascript
import { useState, useCallback } from 'react';

export const useChatStream = () => {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(async (message) => {
    setIsStreaming(true);
    
    // Add user message
    const userMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          conversation_history: messages
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = { role: 'assistant', content: '' };
      
      setMessages(prev => [...prev, assistantMessage]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'token') {
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1].content += data.content;
                return updated;
              });
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
    } finally {
      setIsStreaming(false);
    }
  }, [messages]);

  return { messages, sendMessage, isStreaming };
};
```

### Expected Behavior
- Streaming endpoint returns SSE events
- Regular endpoint returns complete JSON response
- Conversation history is maintained across requests
- CORS headers allow frontend access

---

## Notes

- The API uses FastAPI with automatic OpenAPI documentation
- Visit `http://localhost:8000/docs` for interactive API documentation
- The chatbot uses LangGraph for conversation management
- All endpoints support conversation history for context
