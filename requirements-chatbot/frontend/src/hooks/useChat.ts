import { useState, useEffect, useCallback } from 'react';
import { streamChatResponse, type ChatMessage } from '../services/chatService';

const STORAGE_KEY = 'chatbot-messages';
const MAX_STORED_MESSAGES = 50;

export interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearChat: () => void;
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load messages from localStorage on initialization
  useEffect(() => {
    try {
      const storedMessages = localStorage.getItem(STORAGE_KEY);
      if (storedMessages) {
        const parsed = JSON.parse(storedMessages);
        // Convert timestamp strings back to Date objects
        const messagesWithDates = parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(messagesWithDates);
      }
    } catch (error) {
      console.error('Failed to load messages from localStorage:', error);
    }
  }, []);

  // Save messages to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        // Keep only the last 50 messages
        const messagesToStore = messages.slice(-MAX_STORED_MESSAGES);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(messagesToStore));
      } catch (error) {
        console.error('Failed to save messages to localStorage:', error);
      }
    }
  }, [messages]);

  const generateMessageId = (): string => {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const sendMessage = useCallback(async (messageContent: string) => {
    if (!messageContent.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      role: 'user',
      content: messageContent.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);

    // Create assistant message placeholder
    const assistantMessageId = generateMessageId();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      let accumulatedContent = '';

      await streamChatResponse(
        messageContent.trim(),
        messages, // Pass current conversation history
        {
          onToken: (token: string) => {
            accumulatedContent += token;
            setMessages(prev => 
              prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: accumulatedContent }
                  : msg
              )
            );
          },
          onComplete: (fullMessage: string) => {
            setMessages(prev => 
              prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: fullMessage }
                  : msg
              )
            );
            setIsLoading(false);
          },
          onError: (error: Error) => {
            setError(error.message);
            // Remove the placeholder assistant message on error
            setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
            setIsLoading(false);
          }
        }
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      setError(errorMessage);
      // Remove the placeholder assistant message on error
      setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
      setIsLoading(false);
    }
  }, [messages, isLoading]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear messages from localStorage:', error);
    }
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat
  };
};
