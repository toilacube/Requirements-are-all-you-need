import { useState } from 'react';
import { useChat } from './hooks/useChat';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { MessageList } from './components/chat/MessageList';
import { MessageInput } from './components/chat/MessageInput';
import { ErrorAlert } from './components/chat/ErrorAlert';
import { ClearChatDialog } from './components/chat/ClearChatDialog';
import { Trash2 } from 'lucide-react';

function App() {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();
  const [showClearDialog, setShowClearDialog] = useState(false);

  const handleClearChat = () => {
    clearChat();
    setShowClearDialog(false);
  };

  const handleDismissError = () => {
    // In a real implementation, you might want to add a dismissError function to useChat
    // For now, we'll just refresh the page or handle it differently
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-background container mx-auto p-4">
      <Card className="w-full max-w-4xl mx-auto h-[90vh] flex flex-col">
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-semibold">
              Requirements Chatbot
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowClearDialog(true)}
              disabled={messages.length === 0 || isLoading}
              className="flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Clear Chat
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
          {error && (
            <ErrorAlert 
              error={error} 
              onDismiss={handleDismissError}
            />
          )}
          
          <div className="flex-1 overflow-hidden">
            <MessageList messages={messages} />
          </div>
          
          <MessageInput 
            onSendMessage={sendMessage}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      <ClearChatDialog
        open={showClearDialog}
        onOpenChange={setShowClearDialog}
        onConfirm={handleClearChat}
      />
    </div>
  );
}

export default App;
