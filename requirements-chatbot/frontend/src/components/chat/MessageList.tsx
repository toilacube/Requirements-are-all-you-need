import { useEffect, useRef } from 'react';
import type { ChatMessage } from '../../services/chatService';
import { ScrollArea } from '../ui/scroll-area';
import { MessageItem } from './MessageItem';

interface MessageListProps {
  messages: ChatMessage[];
}

export const MessageList = ({ messages }: MessageListProps) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      });
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
        <div className="flex items-center justify-center h-full min-h-[400px] text-muted-foreground">
          <div className="text-center">
            <div className="text-lg font-medium mb-2">Welcome to the Chatbot!</div>
            <div className="text-sm">Start a conversation by typing a message below.</div>
          </div>
        </div>
      </ScrollArea>
    );
  }

  return (
    <ScrollArea className="h-full" ref={scrollAreaRef}>
      <div className="space-y-1 p-2">
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </ScrollArea>
  );
};
