/**
 * UI FIXTURE DATA ONLY
 * 
 * Notice: The data below represents mock demonstration data for Apple Inc. (AAPL)
 * to validate the frontend presentation layer. It does NOT represent verified or live
 * financial information and is strictly isolated for component testing.
 */

import { FinancialResponseData } from '../types/financial';

export const APPLE_FINANCIAL_FIXTURE: FinancialResponseData = {
  title: 'Apple Inc. (AAPL) — Financial Overview',
  subtitle: 'Comparative Multi-Year Analysis · 2022 – 2025 (Demo Fixture)',
  narrative:
    'Apple demonstrates strong revenue generation and profitability across the selected periods, with operating performance remaining resilient. (UI Fixture / Demo Data)',
  metrics: [
    {
      id: 'metric-rev',
      label: 'Revenue',
      value: '$391.0B',
      change: '+2.0%',
      changeLabel: 'YoY',
      period: 'FY2024',
      trend: 'positive',
    },
    {
      id: 'metric-netinc',
      label: 'Net Income',
      value: '$93.7B',
      change: '-3.4%',
      changeLabel: 'YoY',
      period: 'FY2024',
      trend: 'neutral',
    },
    {
      id: 'metric-eps',
      label: 'EPS',
      value: '$6.08',
      change: '-0.8%',
      changeLabel: 'YoY',
      period: 'FY2024',
      trend: 'neutral',
    },
    {
      id: 'metric-opmargin',
      label: 'Operating Margin',
      value: '31.5%',
      change: '+130 bps',
      changeLabel: 'vs FY23',
      period: 'FY2024',
      trend: 'positive',
    },
  ],
  chart: {
    title: 'Revenue Trend (2022 – 2025)',
    subtitle: 'Reported annual revenue in billions USD (UI Fixture)',
    data: [
      { period: '2022', value: 394.3, formattedValue: '$394.3B' },
      { period: '2023', value: 383.3, formattedValue: '$383.3B' },
      { period: '2024', value: 391.0, formattedValue: '$391.0B' },
      { period: '2025', value: 410.2, formattedValue: '$410.2B' },
    ],
    valueKey: 'value',
    unit: '$B',
  },
  table: {
    title: 'Financial Performance Summary',
    subtitle: 'Annual comparative statement of operations (UI Fixture)',
    columns: [
      { key: 'metric', header: 'Metric', align: 'left' },
      { key: 'y2022', header: '2022', align: 'right', isNumeric: true },
      { key: 'y2023', header: '2023', align: 'right', isNumeric: true },
      { key: 'y2024', header: '2024', align: 'right', isNumeric: true },
      { key: 'y2025', header: '2025', align: 'right', isNumeric: true },
    ],
    rows: [
      {
        id: 'row-revenue',
        metric: 'Revenue',
        values: { y2022: '$394.3B', y2023: '$383.3B', y2024: '$391.0B', y2025: '$410.2B' },
        isHighlight: true,
      },
      {
        id: 'row-netincome',
        metric: 'Net Income',
        values: { y2022: '$99.8B', y2023: '$97.0B', y2024: '$93.7B', y2025: '$104.5B' },
        isHighlight: true,
      },
      {
        id: 'row-eps',
        metric: 'EPS',
        values: { y2022: '$6.11', y2023: '$6.13', y2024: '$6.08', y2025: '$6.85' },
      },
      {
        id: 'row-opmargin',
        metric: 'Operating Margin',
        values: { y2022: '30.3%', y2023: '29.8%', y2024: '31.5%', y2025: '32.1%' },
        isHighlight: true,
      },
    ],
  },
  findings: [
    'Revenue shows a positive recovery trend in the latest period. (Demo finding)',
    'Net income remains strong relative to revenue. (Demo finding)',
    'Operating margin remains structurally healthy. (Demo finding)',
  ],
  source: {
    sourceName: 'Demo fixture — no external financial source connected.',
  },
};
