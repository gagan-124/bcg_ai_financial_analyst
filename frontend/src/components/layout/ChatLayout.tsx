import React from 'react';
import { ChatWindow } from '../chat/ChatWindow';
import { ChatMessage } from '../../types';

export interface ChatLayoutProps {
  messages: ChatMessage[];
  isSubmitting?: boolean;
  onSendMessage: (content: string) => void;
  activeConversationId?: string | null;
  className?: string;
}

export const ChatLayout: React.FC<ChatLayoutProps> = ({
  messages,
  isSubmitting = false,
  onSendMessage,
  activeConversationId,
  className = '',
}) => {
  return (
    <main
      className={`flex-1 min-w-0 flex flex-col h-full overflow-hidden ${className}`.trim()}
    >
      <ChatWindow
        messages={messages}
        isSubmitting={isSubmitting}
        onSendMessage={onSendMessage}
        activeConversationId={activeConversationId}
      />
    </main>
  );
};

export default ChatLayout;


