export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface StreamCallbacks {
  onToken?: (token: string) => void;
  onComplete?: (fullMessage: string) => void;
  onError?: (error: Error) => void;
}

export interface ChatRequest {
  message: string;
  conversation_history: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
  stream_mode?: 'messages' | 'updates' | 'values';
}

const API_BASE_URL = 'http://localhost:8000';

export const streamChatResponse = async (
  message: string,
  conversationHistory: ChatMessage[],
  callbacks: StreamCallbacks
): Promise<void> => {
  const { onToken, onComplete, onError } = callbacks;
  
  try {
    // Convert ChatMessage[] to the API format
    const history = conversationHistory.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    const requestBody: ChatRequest = {
      message,
      conversation_history: history,
      stream_mode: 'messages'
    };

    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Failed to get response reader');
    }

    const decoder = new TextDecoder();
    let fullMessage = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix
            
            if (data.trim() === '') continue;
            
            try {
              const parsed = JSON.parse(data);
              
              if (parsed.type === 'token') {
                fullMessage += parsed.content;
                onToken?.(parsed.content);
              } else if (parsed.type === 'done') {
                onComplete?.(fullMessage);
                return;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', data);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }

    // If we reach here without a 'done' event, complete with what we have
    onComplete?.(fullMessage);
    
  } catch (error) {
    console.error('Chat service error:', error);
    onError?.(error instanceof Error ? error : new Error('Unknown error occurred'));
  }
};
