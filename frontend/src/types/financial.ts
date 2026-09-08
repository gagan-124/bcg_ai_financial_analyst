// Financial analysis data structures and contracts

export type MetricTrend = 'positive' | 'negative' | 'neutral';

export interface MetricItem {
  id?: string;
  label: string;
  value: string;
  change?: string;
  changeLabel?: string;
  period?: string;
  trend?: MetricTrend;
}

export interface FinancialTableColumn {
  key: string;
  header: string;
  align?: 'left' | 'right' | 'center';
  isNumeric?: boolean;
}

export interface FinancialTableRow {
  id: string;
  metric: string;
  values: Record<string, string | number>;
  isHighlight?: boolean;
}

export interface FinancialChartDataPoint {
  period: string;
  value: number;
  formattedValue?: string;
  [key: string]: string | number | undefined;
}

export interface FinancialChartSeries {
  dataKey: string;
  label: string;
  stroke?: string;
}

export interface FinancialChartConfig {
  title?: string;
  subtitle?: string;
  data: FinancialChartDataPoint[];
  valueKey?: string;
  unit?: string;
  series?: FinancialChartSeries[];
}

export interface FinancialTableConfig {
  title?: string;
  subtitle?: string;
  columns: FinancialTableColumn[];
  rows: FinancialTableRow[];
}

export interface SourceCitationData {
  sourceName: string;
  documentType?: string;
  period?: string;
  filingDate?: string;
}

export interface FinancialResponseData {
  title: string;
  subtitle?: string;
  narrative?: string;
  metrics?: MetricItem[];
  chart?: FinancialChartConfig;
  table?: FinancialTableConfig;
  findings?: string[];
  source?: SourceCitationData;
}
