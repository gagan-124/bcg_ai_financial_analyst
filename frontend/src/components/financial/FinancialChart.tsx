import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  TooltipProps,
} from 'recharts';
import { FinancialChartDataPoint, FinancialChartSeries } from '../../types/financial';

export interface FinancialChartProps {
  data: FinancialChartDataPoint[];
  valueKey?: string;
  unit?: string;
  height?: number;
  className?: string;
  series?: FinancialChartSeries[];
}

interface CustomTooltipProps extends TooltipProps<number, string> {
  unit?: string;
}

const ChartTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, unit }) => {
  if (active && payload && payload.length) {
    if (payload.length > 1) {
      return (
        <div
          className="bg-surface border border-border-hairline rounded-md px-3 py-2 shadow-neumorphic-elevated select-none space-y-1"
          role="tooltip"
        >
          <span className="block text-[11px] font-medium text-text-muted tracking-wide border-b border-border-hairline/60 pb-1">
            Period: {label}
          </span>
          {payload.map((item, idx) => {
            const dataPoint = item.payload as FinancialChartDataPoint;
            const displayValue =
              dataPoint[`${item.dataKey}_formatted`] ??
              (unit ? `${item.value} ${unit}` : `${item.value}`);
            return (
              <div key={idx} className="flex items-center justify-between gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-text-secondary">
                  <span
                    className="w-2 h-2 rounded-full inline-block"
                    style={{ backgroundColor: item.color }}
                  />
                  {item.name || item.dataKey}:
                </span>
                <span className="font-semibold tabular-nums text-text-primary">
                  {displayValue}
                </span>
              </div>
            );
          })}
        </div>
      );
    }

    const item = payload[0];
    const dataPoint = item.payload as FinancialChartDataPoint;
    const displayValue =
      dataPoint.formattedValue ?? (unit ? `${item.value} ${unit}` : `${item.value}`);

    return (
      <div
        className="bg-surface border border-border-hairline rounded-md px-3 py-1.5 shadow-neumorphic-elevated select-none"
        role="tooltip"
      >
        <span className="block text-[11px] font-medium text-text-muted tracking-wide">
          {label}
        </span>
        <span className="block text-xs font-semibold tabular-nums text-text-primary mt-0.5">
          {displayValue}
        </span>
      </div>
    );
  }
  return null;
};

export const FinancialChart: React.FC<FinancialChartProps> = ({
  data,
  valueKey = 'value',
  unit = '',
  height = 200,
  className = '',
  series,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-44 flex items-center justify-center text-xs text-text-muted border border-dashed border-border-hairline rounded">
        No trend data available
      </div>
    );
  }

  const palette = ['#8BBB92', '#5D8480', '#9EBDB9', '#3D6E68'];

  return (
    <div
      className={`w-full ${className}`.trim()}
      role="region"
      aria-label="Financial Trend Chart"
    >
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 10, right: 12, left: -16, bottom: 0 }}
          >
            {/* Subtle, restrained institutional grid */}
            <CartesianGrid
              stroke="rgba(255, 255, 255, 0.05)"
              strokeDasharray="3 3"
              vertical={false}
            />

            {/* Clean X Axis */}
            <XAxis
              dataKey="period"
              stroke="rgba(255, 255, 255, 0.1)"
              tick={{ fill: '#9EBDB9', fontSize: 11, fontFamily: 'Supreme, sans-serif' }}
              tickLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              dy={6}
            />

            {/* Subtle Y Axis with tabular figures */}
            <YAxis
              stroke="rgba(255, 255, 255, 0.1)"
              tick={{ fill: '#5D8480', fontSize: 10, fontFamily: 'Supreme, sans-serif' }}
              tickLine={false}
              axisLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(val) => (unit ? `${val}` : `${val}`)}
            />

            {/* Custom institutional tooltip */}
            <Tooltip
              content={<ChartTooltip unit={unit} />}
              cursor={{ stroke: 'rgba(139, 187, 146, 0.25)', strokeWidth: 1 }}
            />

            {/* Render multiple lines if series is provided, otherwise single line */}
            {series && series.length > 0 ? (
              series.map((s, idx) => {
                const strokeColor = s.stroke || palette[idx % palette.length];
                return (
                  <Line
                    key={s.dataKey}
                    type="monotone"
                    name={s.label}
                    dataKey={s.dataKey}
                    stroke={strokeColor}
                    strokeWidth={2}
                    dot={{
                      r: 3.5,
                      fill: strokeColor,
                      stroke: '#12544F',
                      strokeWidth: 1.5,
                    }}
                    activeDot={{
                      r: 5,
                      fill: strokeColor,
                      stroke: '#092328',
                      strokeWidth: 2,
                    }}
                    isAnimationActive={false}
                  />
                );
              })
            ) : (
              <Line
                type="monotone"
                dataKey={valueKey}
                stroke="#8BBB92"
                strokeWidth={2}
                dot={{
                  r: 3.5,
                  fill: '#8BBB92',
                  stroke: '#12544F',
                  strokeWidth: 1.5,
                }}
                activeDot={{
                  r: 5,
                  fill: '#8BBB92',
                  stroke: '#092328',
                  strokeWidth: 2,
                }}
                isAnimationActive={false}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default FinancialChart;
