import { Alert, AlertDescription } from '../ui/alert';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from '../ui/button';

interface ErrorAlertProps {
  error: string;
  onDismiss: () => void;
}

export const ErrorAlert = ({ error, onDismiss }: ErrorAlertProps) => {
  return (
    <Alert variant="destructive" className="mx-4 mb-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <span>{error}</span>
        <Button
          variant="outline"
          size="sm"
          onClick={onDismiss}
          className="h-auto p-1 hover:bg-destructive/20"
        >
          <X className="h-3 w-3" />
        </Button>
      </AlertDescription>
    </Alert>
  );
};
