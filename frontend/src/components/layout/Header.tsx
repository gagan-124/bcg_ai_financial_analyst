import React from 'react';
import { Menu, SlidersHorizontal, User } from 'lucide-react';

export interface HeaderProps {
  onToggleSidebar?: () => void;
  className?: string;
}

export const Header: React.FC<HeaderProps> = ({
  onToggleSidebar,
  className = '',
}) => {
  return (
    <header
      className={`h-12 w-full px-4 border-b border-border-hairline bg-app/95 flex items-center justify-between select-none shrink-0 ${className}`.trim()}
    >
      {/* Left: Context & Mobile Menu Trigger */}
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="p-1.5 rounded-sm text-text-muted hover:text-text-primary hover:bg-surface md:hidden transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive"
            aria-label="Toggle navigation sidebar"
          >
            <Menu className="w-[18px] h-[18px]" />
          </button>
        )}
        <span className="text-sm font-medium text-text-secondary tracking-wide">
          Financial Analyst
        </span>
      </div>

      {/* Right: Restrained System Status & Utilities */}
      <div className="flex items-center gap-3">
        {/* Status Indicator */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-sm bg-surface/40 border border-border-hairline">
          <span
            className="w-1.5 h-1.5 rounded-full bg-accent-sage"
            aria-hidden="true"
          />
          <span className="text-xs font-normal text-text-secondary tracking-tight">
            Connected
          </span>
        </div>

        {/* Minimal Utilities with 18-20px icons */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            className="p-1.5 rounded-sm text-text-muted hover:text-text-primary hover:bg-surface transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive"
            aria-label="Configuration and filters"
          >
            <SlidersHorizontal className="w-[19px] h-[19px]" />
          </button>
          <button
            type="button"
            className="p-1.5 rounded-sm text-text-muted hover:text-text-primary hover:bg-surface transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary-interactive"
            aria-label="User profile"
          >
            <User className="w-[19px] h-[19px]" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
