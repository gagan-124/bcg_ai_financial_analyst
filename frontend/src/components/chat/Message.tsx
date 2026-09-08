import React from 'react';
import { Bot, User as UserIcon, AlertCircle } from 'lucide-react';
import { MessageRole, FinancialResponseData } from '../../types';
import { FinancialResponse } from '../financial';

export interface MessageProps {
  id?: string;
  role: MessageRole;
  content: string;
  createdAt?: string;
  isLoading?: boolean;
  status?: 'sending' | 'sent' | 'error';
  financialResponse?: FinancialResponseData;
  financialData?: FinancialResponseData;
  className?: string;
}

export const Message: React.FC<MessageProps> = ({
  role,
  content,
  createdAt,
  isLoading = false,
  status = 'sent',
  financialResponse,
  financialData,
  className = '',
}) => {
  const isUser = role === 'user';
  const isSystem = role === 'system';
  const isError = status === 'error';
  const financial = financialResponse ?? financialData;
  const hasFinancialData = Boolean(financial);

  if (isSystem) {
    return (
      <div className={`flex justify-center my-3 ${className}`.trim()}>
        <span className="px-3 py-1 text-xs text-text-muted bg-surface/40 border border-border-hairline rounded-sm">
          {content}
        </span>
      </div>
    );
  }

  return (
    <article
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} ${className}`.trim()}
      aria-label={`${isUser ? 'User' : 'BCG AI Financial Analyst'} message`}
    >
      <div
        className={`flex gap-3 ${
          hasFinancialData
            ? 'w-full max-w-full md:max-w-[92%]'
            : isUser
            ? 'max-w-[90%] md:max-w-[80%] flex-row-reverse'
            : 'max-w-[90%] md:max-w-[80%] flex-row'
        }`}
      >
        {/* Identity Icon / Avatar */}
        <div
          className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 border select-none ${
            isUser
              ? 'bg-surface border-border-hairline text-text-secondary'
              : isError
              ? 'bg-red-950/40 border-red-500/40 text-red-400'
              : 'bg-surface/90 border-border-subtle text-accent-sage shadow-neumorphic-card'
          }`}
          aria-hidden="true"
        >
          {isUser ? (
            <UserIcon className="w-3.5 h-3.5" />
          ) : isError ? (
            <AlertCircle className="w-4 h-4" />
          ) : (
            <Bot className="w-4 h-4" />
          )}
        </div>

        {/* Message Container & Content */}
        <div className={`space-y-1 ${isUser ? 'text-right' : 'text-left'} flex-1 min-w-0`}>
          {/* Header Metadata */}
          <div
            className={`flex items-center gap-2 text-[11px] font-medium tracking-tight text-text-muted ${
              isUser ? 'justify-end' : 'justify-start'
            }`}
          >
            <span>{isUser ? 'You' : isError ? 'System Notice' : 'BCG AI Financial Analyst'}</span>
            {createdAt && <span className="tabular-nums opacity-75">{createdAt}</span>}
          </div>

          {/* Body Content */}
          <div
            className={`rounded-lg transition-colors ${
              isUser
                ? 'bg-surface/85 text-text-primary border border-border-hairline shadow-neumorphic-card px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words inline-block'
                : isError
                ? 'bg-red-950/20 text-red-200 border border-red-500/30 px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words'
                : hasFinancialData
                ? 'bg-surface/20 text-text-primary border border-border-hairline/80 shadow-sm p-4 md:p-5 w-full'
                : 'bg-surface/30 text-text-primary border border-border-hairline/80 shadow-sm px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words'
            }`}
          >
            {content && (!financial || content !== financial.narrative) && (
              <div
                className={`text-sm leading-relaxed whitespace-pre-wrap break-words ${
                  hasFinancialData ? 'mb-4 pb-3 border-b border-border-hairline/60' : ''
                }`}
              >
                {content}
                {isLoading && !hasFinancialData && (
                  <span className="inline-block ml-2 w-1.5 h-3 bg-accent-sage animate-pulse" />
                )}
              </div>
            )}

            {financial && <FinancialResponse data={financial} />}

            {isLoading && hasFinancialData && (
              <span className="inline-block mt-2 w-1.5 h-3 bg-accent-sage animate-pulse" />
            )}
          </div>
        </div>
      </div>
    </article>
  );
};

export default Message;
