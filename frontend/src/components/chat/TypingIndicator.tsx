import React from 'react';
import { Bot } from 'lucide-react';

export interface TypingIndicatorProps {
  className?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ className = '' }) => {
  return (
    <div
      className={`flex w-full justify-start select-none ${className}`.trim()}
      role="status"
      aria-label="Assistant is processing"
    >
      <div className="flex gap-3 max-w-[90%] md:max-w-[78%] items-start">
        {/* Assistant Identity Avatar */}
        <div
          className="w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 border bg-surface/90 border-border-subtle text-accent-sage shadow-neumorphic-card"
          aria-hidden="true"
        >
          <Bot className="w-4 h-4" />
        </div>

        {/* Typing Bubble */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-[11px] font-medium tracking-tight text-text-muted">
            <span>BCG AI Financial Analyst</span>
            <span className="text-[10px] text-accent-sage tracking-wider uppercase">Processing</span>
          </div>

          <div className="rounded-lg px-4 py-3 bg-surface/40 border border-border-hairline shadow-sm inline-flex items-center gap-1.5 h-10">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-sage animate-pulse motion-reduce:animate-none" />
            <span
              className="w-1.5 h-1.5 rounded-full bg-accent-sage animate-pulse motion-reduce:animate-none"
              style={{ animationDelay: '150ms' }}
            />
            <span
              className="w-1.5 h-1.5 rounded-full bg-accent-sage animate-pulse motion-reduce:animate-none"
              style={{ animationDelay: '300ms' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
