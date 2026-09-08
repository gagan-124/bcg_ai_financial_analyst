import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

export interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about corporate financials, SEC filings, or metrics...',
  className = '',
}) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSubmit = value.trim().length > 0 && !disabled;

  // Auto-resize textarea height to accommodate multi-line input up to ~160px
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const scrollHeight = textarea.scrollHeight;
    textarea.style.height = `${Math.min(Math.max(scrollHeight, 44), 160)}px`;
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [value]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!canSubmit) return;

    const trimmed = value.trim();
    if (trimmed) {
      onSend(trimmed);
      setValue('');
      if (textareaRef.current) {
        textareaRef.current.style.height = '44px';
      }
      // Keep input focused so the user can immediately continue typing
      requestAnimationFrame(() => {
        textareaRef.current?.focus();
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`relative w-full max-w-content mx-auto rounded-lg bg-surface/40 border border-border-hairline shadow-neumorphic-inset transition-all duration-150 focus-within:border-border-subtle focus-within:ring-1 focus-within:ring-primary-interactive ${className}`.trim()}
    >
      <div className="flex items-end px-3 py-2 gap-2">
        <label htmlFor="chat-message-input" className="sr-only">
          Ask a financial question
        </label>
        <textarea
          ref={textareaRef}
          id="chat-message-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus
          rows={1}
          className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted resize-none border-0 focus:outline-none focus:ring-0 leading-relaxed py-1.5 px-1 max-h-40 min-h-[28px] overflow-y-auto"
        />

        <button
          type="submit"
          disabled={!canSubmit}
          className="h-8 w-8 rounded-md bg-primary-interactive text-text-primary shadow-neumorphic-card border border-white/[0.08] flex items-center justify-center shrink-0 transition-all duration-150 hover:bg-primary-hover active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-sage"
          aria-label="Send message"
        >
          <ArrowUp className="w-4 h-4" />
        </button>
      </div>
    </form>
  );
};

export default MessageInput;
