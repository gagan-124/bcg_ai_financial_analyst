import React from 'react';
import { FinancialResponseData } from '../../types/financial';
import { MetricCard } from './MetricCard';
import { FinancialCard } from './FinancialCard';
import { FinancialTable } from './FinancialTable';
import { FinancialChart } from './FinancialChart';
import { SourceCitation } from './SourceCitation';

export interface FinancialResponseProps {
  data: FinancialResponseData;
  className?: string;
}

export const FinancialResponse: React.FC<FinancialResponseProps> = ({
  data,
  className = '',
}) => {
  const {
    title,
    subtitle,
    narrative,
    metrics,
    chart,
    table,
    findings,
    source,
  } = data;

  return (
    <div className={`space-y-4 w-full ${className}`.trim()}>
      {/* 1. Response Header: Title & Subtitle */}
      {(title || subtitle) && (
        <div className="border-b border-border-hairline pb-2.5">
          {title && (
            <h2 className="text-sm md:text-base font-semibold text-text-primary tracking-tight">
              {title}
            </h2>
          )}
          {subtitle && (
            <p className="text-xs text-text-muted mt-0.5">
              {subtitle}
            </p>
          )}
        </div>
      )}

      {/* 2. Narrative Analysis */}
      {narrative && (
        <p className="text-sm text-text-primary leading-relaxed">
          {narrative}
        </p>
      )}

      {/* 3. Key Metrics Grid */}
      {metrics && metrics.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
          {metrics.map((metric, idx) => (
            <MetricCard
              key={metric.id ?? `metric-${idx}`}
              label={metric.label}
              value={metric.value}
              change={metric.change}
              changeLabel={metric.changeLabel}
              period={metric.period}
              trend={metric.trend}
            />
          ))}
        </div>
      )}

      {/* 4. Financial Trend Chart */}
      {chart && chart.data && chart.data.length > 0 && (
        <FinancialCard
          title={chart.title ?? 'Trend Analysis'}
          subtitle={chart.subtitle}
        >
          <FinancialChart
            data={chart.data}
            valueKey={chart.valueKey ?? 'value'}
            series={chart.series}
            unit={chart.unit}
            height={200}
          />
        </FinancialCard>
      )}

      {/* 5. Detailed Financial Table */}
      {table && table.columns && table.rows && (
        <FinancialCard
          title={table.title ?? 'Financial Breakdown'}
          subtitle={table.subtitle}
        >
          <FinancialTable
            columns={table.columns}
            rows={table.rows}
            caption={table.title}
          />
        </FinancialCard>
      )}

      {/* 6. Structured Key Findings */}
      {findings && findings.length > 0 && (
        <div className="bg-surface/40 border border-border-hairline rounded-md p-3.5 space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Key Findings
          </h3>
          <ul className="space-y-1.5 text-xs text-text-primary">
            {findings.map((finding, idx) => (
              <li key={idx} className="flex items-start gap-2 leading-relaxed">
                <span className="text-accent-sage mt-0.5 select-none" aria-hidden="true">
                  •
                </span>
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 7. Restrained Source Citation */}
      {source && (
        <div className="pt-1">
          <SourceCitation source={source} />
        </div>
      )}
    </div>
  );
};

export default FinancialResponse;
