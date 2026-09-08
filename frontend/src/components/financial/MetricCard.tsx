import React from 'react';
import { MetricTrend } from '../../types/financial';

export interface MetricCardProps {
  label: string;
  value: string;
  change?: string;
  changeLabel?: string;
  period?: string;
  trend?: MetricTrend;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  change,
  changeLabel,
  period,
  trend = 'neutral',
  className = '',
}) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'positive':
        return 'text-accent-sage';
      case 'negative':
        return 'text-text-secondary';
      case 'neutral':
      default:
        return 'text-text-muted';
    }
  };

  return (
    <div
      className={`bg-surface/75 border border-border-hairline rounded-md p-3.5 shadow-neumorphic-card flex flex-col justify-between transition-colors duration-150 ${className}`.trim()}
      role="region"
      aria-label={`${label}: ${value}`}
    >
      {/* Top Header: Label + Optional Period Badge */}
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-[11px] font-medium tracking-wider uppercase text-text-secondary truncate">
          {label}
        </span>
        {period && (
          <span className="text-[10px] font-medium tabular-nums text-text-muted bg-surface/50 border border-border-hairline px-1.5 py-0.5 rounded shrink-0">
            {period}
          </span>
        )}
      </div>

      {/* Main Metric Figure */}
      <div className="text-xl md:text-2xl font-semibold tabular-nums text-text-primary tracking-tight my-0.5">
        {value}
      </div>

      {/* Footer: Trend Change & Context Label */}
      {(change || changeLabel) && (
        <div className="flex items-center gap-1.5 text-xs tabular-nums mt-1 font-medium">
          {change && (
            <span className={`inline-flex items-center gap-0.5 ${getTrendColor()}`}>
              {trend === 'positive' && <span aria-hidden="true">↑</span>}
              {trend === 'negative' && <span aria-hidden="true">↓</span>}
              <span>{change}</span>
            </span>
          )}
          {changeLabel && (
            <span className="text-text-muted text-[11px] font-normal">
              {changeLabel}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default MetricCard;
