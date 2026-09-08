import React from 'react';
import { FinancialTableColumn, FinancialTableRow } from '../../types/financial';

export interface FinancialTableProps {
  columns: FinancialTableColumn[];
  rows: FinancialTableRow[];
  caption?: string;
  className?: string;
}

export const FinancialTable: React.FC<FinancialTableProps> = ({
  columns,
  rows,
  caption,
  className = '',
}) => {
  return (
    <div className={`w-full overflow-hidden ${className}`.trim()}>
      {/* Scrollable Container to prevent page-level horizontal overflow */}
      <div className="w-full overflow-x-auto custom-scrollbar">
        <table
          className="w-full text-xs text-left border-collapse min-w-[480px]"
          aria-label={caption ?? 'Financial Performance Table'}
        >
          <thead>
            <tr className="border-b border-border-hairline text-text-secondary text-[11px] font-medium tracking-wider uppercase">
              {columns.map((col) => {
                const alignClass =
                  col.align === 'right' || col.isNumeric
                    ? 'text-right'
                    : col.align === 'center'
                    ? 'text-center'
                    : 'text-left';

                return (
                  <th
                    key={col.key}
                    scope="col"
                    className={`py-2.5 px-3 font-medium ${alignClass}`}
                  >
                    {col.header}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-hairline/40">
            {rows.map((row) => (
              <tr
                key={row.id}
                className={`transition-colors duration-100 hover:bg-surface-hover/30 ${
                  row.isHighlight ? 'bg-surface/35 font-medium' : ''
                }`}
              >
                {columns.map((col) => {
                  const isFirst = col.key === 'metric';
                  const value = isFirst ? row.metric : row.values[col.key] ?? '—';
                  const alignClass =
                    col.align === 'right' || col.isNumeric
                      ? 'text-right tabular-nums'
                      : col.align === 'center'
                      ? 'text-center'
                      : 'text-left';

                  return (
                    <td
                      key={`${row.id}-${col.key}`}
                      className={`py-2 px-3 whitespace-nowrap ${alignClass} ${
                        row.isHighlight
                          ? 'text-text-primary'
                          : isFirst
                          ? 'text-text-primary'
                          : 'text-text-secondary'
                      }`}
                    >
                      {value}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default FinancialTable;
