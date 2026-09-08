import React from 'react';

export interface FinancialCardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const FinancialCard: React.FC<FinancialCardProps> = ({
  title,
  subtitle,
  children,
  footer,
  action,
  className = '',
}) => {
  return (
    <section
      className={`bg-surface/60 border border-border-hairline rounded-md p-4 shadow-neumorphic-card transition-colors duration-150 ${className}`.trim()}
      aria-label={title}
    >
      {/* Optional Card Header */}
      {(title || subtitle || action) && (
        <div className="flex items-start justify-between gap-3 mb-3.5 pb-2.5 border-b border-border-hairline/60">
          <div className="min-w-0">
            {title && (
              <h3 className="text-xs md:text-sm font-semibold text-text-primary tracking-tight truncate">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-[11px] text-text-muted mt-0.5 truncate">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}

      {/* Main Content Area */}
      <div className="min-w-0">{children}</div>

      {/* Optional Footer */}
      {footer && (
        <div className="mt-3 pt-2.5 border-t border-border-hairline/60 text-[11px] text-text-muted">
          {footer}
        </div>
      )}
    </section>
  );
};

export default FinancialCard;
