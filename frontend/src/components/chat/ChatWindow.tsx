import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../../types';
import { Message } from './Message';
import { MessageInput } from './MessageInput';
import { SuggestedPrompts } from './SuggestedPrompts';
import { TypingIndicator } from './TypingIndicator';

export interface ChatWindowProps {
  messages: ChatMessage[];
  isSubmitting?: boolean;
  onSendMessage: (content: string) => void;
  activeConversationId?: string | null;
  className?: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isSubmitting = false,
  onSendMessage,
  activeConversationId: _activeConversationId,
  className = '',
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting]);

  return (
    <div className={`flex flex-col h-full w-full overflow-hidden ${className}`.trim()}>
      {/* Scrollable Conversation Feed / Empty State */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 md:px-8 py-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 space-y-8 select-none">
            {/* Centered Empty State Header */}
            <div className="max-w-md text-center space-y-2">
              <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-text-primary">
                Financial Analysis
              </h1>
              <p className="text-sm md:text-base text-text-secondary leading-relaxed">
                Analyze company financials through natural language.
              </p>
            </div>

            {/* Reusable Suggested Financial Prompts */}
            <SuggestedPrompts
              onSelectPrompt={onSendMessage}
              disabled={isSubmitting}
            />
          </div>
        ) : (
          <div className="max-w-content mx-auto space-y-5 pb-2">
            {messages.map((message) => (
              <Message
                key={message.id}
                id={message.id}
                role={message.role}
                content={message.content}
                createdAt={message.createdAt}
                status={message.status}
                financialResponse={message.financialResponse}
                financialData={message.financialData}
              />
            ))}

            {isSubmitting && <TypingIndicator />}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>
        )}
      </div>

      {/* Anchored Composer Area */}
      <div className="p-4 md:px-8 border-t border-border-hairline bg-app/95 shrink-0">
        <MessageInput
          onSend={onSendMessage}
          disabled={isSubmitting}
        />
      </div>
    </div>
  );
};

export default ChatWindow;
