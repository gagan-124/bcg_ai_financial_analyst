import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
  className?: string;
}

export const SUGGESTED_PROMPTS = [
  "Analyze Apple's revenue growth",
  "What are Microsoft's key financial trends?",
  "Compare Tesla's profitability",
] as const;

export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({
  onSelectPrompt,
  disabled = false,
  className = '',
}) => {
  return (
    <div
      className={`w-full max-w-xl mx-auto flex flex-col sm:flex-row flex-wrap items-center justify-center gap-2.5 ${className}`.trim()}
      role="group"
      aria-label="Suggested financial prompts"
    >
      {SUGGESTED_PROMPTS.map((prompt) => (
        <button
          key={prompt}
          type="button"
          disabled={disabled}
          onClick={() => onSelectPrompt(prompt)}
          className="group flex items-center justify-between gap-2 px-3.5 py-2 text-xs md:text-sm font-medium text-text-secondary hover:text-text-primary bg-surface/50 hover:bg-surface border border-border-hairline hover:border-border-subtle rounded-md shadow-neumorphic-card transition-all duration-150 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed text-left focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive"
        >
          <span>{prompt}</span>
          <ArrowUpRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent-sage transition-colors duration-150 shrink-0" />
        </button>
      ))}
    </div>
  );
};

export default SuggestedPrompts;
