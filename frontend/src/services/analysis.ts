/**
 * Financial analysis API client service.
 * Connects the frontend to the FastAPI /api/analysis endpoint.
 */

import {
  FinancialResponseData,
  MetricItem,
  FinancialChartDataPoint,
  FinancialTableColumn,
  FinancialTableRow,
  FinancialChartConfig,
  FinancialTableConfig,
  SourceCitationData,
} from '../types/financial';

export interface BackendCompanyInfo {
  name: string;
  ticker: string;
}

export interface BackendFinancialMetric {
  name: string;
  value: string;
  raw_value?: number | null;
  unit?: string | null;
  period?: string | null;
  change?: string | null;
  change_label?: string | null;
  trend?: string | null;
}

export interface BackendFinancialPeriod {
  period: string;
  revenue: number;
  revenue_formatted: string;
  net_income: number;
  net_income_formatted: string;
  eps: number;
  eps_formatted: string;
  operating_margin: number;
  operating_margin_formatted: string;
}

export interface BackendFinancialFinding {
  text: string;
  type: string;
}

export interface BackendSourceInfo {
  name: string;
  type: string;
  document_type?: string | null;
  period?: string | null;
  reference?: string | null;
}

export interface BackendFinancialAnalysisResponse {
  company: BackendCompanyInfo;
  summary: string;
  metrics: BackendFinancialMetric[];
  trend: BackendFinancialPeriod[];
  table: BackendFinancialPeriod[];
  findings: BackendFinancialFinding[];
  source: BackendSourceInfo;
}

export interface BackendFinancialQuestionResponse {
  company: BackendCompanyInfo;
  question: string;
  answer: string;
  source: BackendSourceInfo;
  chart?: FinancialChartConfig | null;
  table?: FinancialTableConfig | null;
  metrics?: BackendFinancialMetric[] | null;
}

export type QueryIntent = 'analysis' | 'question';

export interface ClassifiedQuery {
  intent: QueryIntent;
  company: string;
}

/**
 * Detects if a supported company/ticker is mentioned in the input string.
 * Supports canonical names, tickers, possessives (Apple's), and plurals (apples).
 * When multiple companies are mentioned, prioritizes active company if present,
 * or the company appearing earliest in the text.
 */
export function detectKnownCompany(input: string, preferActive?: string): string | null {
  const lower = input.toLowerCase();
  const companies: { name: string; index: number }[] = [];

  const teslaMatch = lower.search(/\b(tesla|teslas|tsla)('?s)?\b/i);
  if (teslaMatch !== -1) companies.push({ name: 'Tesla', index: teslaMatch });

  const msftMatch = lower.search(/\b(microsoft|microsofts|msft)('?s)?\b/i);
  if (msftMatch !== -1) companies.push({ name: 'Microsoft', index: msftMatch });

  const appleMatch = lower.search(/\b(apple|apples|aapl)('?s)?\b/i);
  if (appleMatch !== -1) companies.push({ name: 'Apple', index: appleMatch });

  if (companies.length === 0) return null;

  // If one of the mentioned companies matches the active conversation company, prioritize it
  if (preferActive) {
    const activeLower = preferActive.toLowerCase();
    const activeMatch = companies.find((c) => activeLower.includes(c.name.toLowerCase()));
    if (activeMatch) return activeMatch.name;
  }

  // Otherwise pick the company mentioned first in the sentence
  companies.sort((a, b) => a.index - b.index);
  return companies[0].name;
}

/**
 * Normalizes company names or tickers to canonical names ('Apple', 'Microsoft', 'Tesla').
 */
export function canonicalizeCompany(input?: string): string | null {
  if (!input) return null;
  return detectKnownCompany(input);
}

/**
 * Lightweight helper to extract target company identifier from user conversational inputs.
 * If a known company is detected (Apple, Microsoft, Tesla), returns canonical name.
 * Otherwise returns cleaned input for backend resolver to evaluate.
 */
export function extractCompany(input: string): string {
  const detected = detectKnownCompany(input);
  if (detected) return detected;

  const cleaned = input
    .replace(
      /^(please\s+)?(analyze|analyse|show|compare|explain|give me|get|what is|what's|tell me about)\s+/i,
      ''
    )
    .replace(
      /(\s+financials?|\s+financial performance|\s+stock|\s+revenue|\s+net income|\s+profit|\s+margin)?\??$/i,
      ''
    )
    .replace(/'s$/i, '')
    .trim();

  return cleaned || input.trim();
}

/**
 * Determines whether a message expresses a follow-up or analytical financial question.
 */
export function isFinancialQuestion(content: string): boolean {
  const trimmed = content.trim();
  const lower = trimmed.toLowerCase();

  // Question starters / interrogative phrasing
  if (
    /^(why|what|how|when|where|which|who|can|could|would|should|is|are|was|were|did|does|do|compare|explain|tell\s+me|describe)\b/i.test(
      trimmed
    )
  ) {
    return true;
  }

  // Question mark
  if (trimmed.endsWith('?')) {
    return true;
  }

  // Interrogative patterns within query
  if (
    /\b(why did|what caused|how did|what changed|what are|explain why|tell me why|tell me about|how come|compare\b)/i.test(
      lower
    )
  ) {
    return true;
  }

  // Inquires about metric movement/reasons
  const hasMetric = /\b(net income|operating margin|revenue|profitability|earnings|eps|margins?|growth)\b/i.test(
    lower
  );
  const hasTrend = /\b(increase|decrease|growth|grow|decline|drop|change|down|up|fall|rose|risen|higher|lower|expand|compress)\b/i.test(
    lower
  );
  if (hasMetric && hasTrend) {
    return true;
  }

  return false;
}

/**
 * Determines whether a message is an explicit request for a new company overview/analysis.
 */
export function isNewAnalysisRequest(content: string): boolean {
  const trimmed = content.trim();

  // Questions are never new company analysis requests
  if (isFinancialQuestion(trimmed)) {
    return false;
  }

  // Standalone company or ticker name
  if (
    /^(apple|apples|apple's|aapl|microsoft|microsofts|microsoft's|msft|tesla|teslas|tesla's|tsla)$/i.test(
      trimmed.replace(/[!.,?]+$/, '')
    )
  ) {
    return true;
  }

  // Direct analysis commands (e.g. "Analyze Apple", "Analyze Tesla's financial performance")
  if (/^(please\s+)?(analyze|analyse)\s+/i.test(trimmed)) {
    return true;
  }

  // Request for overview/financials
  if (
    /^(please\s+)?(show|give|display|provide|pull\s+up)(\s+me)?\s+(an?\s+)?(analysis|overview|financials?|financial\s+performance|financial\s+overview)\s+(of|for)\s+/i.test(
      trimmed
    )
  ) {
    return true;
  }

  // Company possessive financials (e.g. "Show me Apple's financials", "Show Apple financials")
  if (
    /^(please\s+)?(show|give|display|provide|pull\s+up)(\s+me)?\s+(.+?)('?s)?\s+(financials?|financial\s+performance|financial\s+overview|statements?|metrics)\b/i.test(
      trimmed
    )
  ) {
    return true;
  }

  if (/^(financial\s+overview|financial\s+analysis|company\s+overview)\s+(of|for)\s+/i.test(trimmed)) {
    return true;
  }

  return false;
}

/**
 * Intent-first query classifier.
 *
 * 1. Financial Questions:
 *    Always route to the Gemini question layer.
 *    - If question explicitly names a company (e.g. "Why did Apple's net income increase?"), uses that company.
 *    - If question omits company name (e.g. "Why did operating margin increase?"), uses active company from context.
 *
 * 2. New Company Analysis:
 *    Routes to /api/analysis only when user specifically requests an analysis or overview.
 *    - Switches active company context when user commands a new company analysis.
 */
export function classifyQueryIntent(
  content: string,
  activeCompany?: string
): ClassifiedQuery {
  const trimmed = content.trim();
  const detectedCompany = detectKnownCompany(trimmed, activeCompany);
  const activeCanonical = canonicalizeCompany(activeCompany);

  // 1. INTENT-FIRST: Is this a financial question?
  if (isFinancialQuestion(trimmed)) {
    const extracted = extractCompany(trimmed);
    const targetCompany = detectedCompany || activeCanonical || extracted || 'Apple';
    return {
      intent: 'question',
      company: targetCompany,
    };
  }

  // 2. Is this an explicit company analysis request?
  if (isNewAnalysisRequest(trimmed)) {
    const targetCompany = detectedCompany || activeCanonical || extractCompany(trimmed);
    return {
      intent: 'analysis',
      company: targetCompany,
    };
  }

  // 3. Fallback within an active company chat: general follow-up text is treated as a question
  if (activeCanonical) {
    return {
      intent: 'question',
      company: detectedCompany || activeCanonical,
    };
  }

  // 4. Fresh chat with recognized company: default to analysis
  if (detectedCompany) {
    return {
      intent: 'analysis',
      company: detectedCompany,
    };
  }

  // Ambiguous query in fresh chat: attempt company extraction
  return {
    intent: 'analysis',
    company: extractCompany(trimmed),
  };
}

/**
 * Call FastAPI financial analysis endpoint.
 */
export async function analyzeCompany(
  company: string,
  query?: string,
  apiBaseUrl: string = import.meta.env.VITE_API_BASE_URL || ''
): Promise<BackendFinancialAnalysisResponse> {
  const payload: { company: string; query?: string } = { company };
  if (query) {
    payload.query = query;
  }

  const endpoint = apiBaseUrl
    ? `${apiBaseUrl.replace(/\/$/, '')}/api/analysis`
    : '/api/analysis';

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Financial analysis request failed with status ${response.status}`
    );
  }

  return response.json();
}

/**
 * Call FastAPI follow-up question endpoint.
 */
export async function askFinancialQuestion(
  company: string,
  question: string,
  apiBaseUrl: string = import.meta.env.VITE_API_BASE_URL || ''
): Promise<BackendFinancialQuestionResponse> {
  const t0 = performance.now();
  console.log(`[FRONTEND QUESTION] request started for ${company}`);
  const payload = { company, question };
  const endpoint = apiBaseUrl
    ? `${apiBaseUrl.replace(/\/$/, '')}/api/analysis/question`
    : '/api/analysis/question';

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const tFetch = performance.now();
  console.log(`[FRONTEND QUESTION] network fetch returned: ${(tFetch - t0).toFixed(1)} ms`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Financial question request failed with status ${response.status}`
    );
  }

  const data = await response.json();
  const tParse = performance.now();
  console.log(
    `[FRONTEND QUESTION] response parsing: ${(tParse - tFetch).toFixed(1)} ms (total frontend roundtrip: ${(tParse - t0).toFixed(1)} ms)`
  );
  return data;
}

/**
 * Maps backend analysis response into the existing frontend FinancialResponseData schema.
 */
export function mapBackendToFrontendResponse(
  backendData: BackendFinancialAnalysisResponse
): FinancialResponseData {
  const metrics: MetricItem[] = backendData.metrics.map((m, idx) => ({
    id: `backend-metric-${idx}`,
    label: m.name,
    value: m.value,
    change: m.change ?? undefined,
    changeLabel: m.change_label ?? undefined,
    period: m.period ?? undefined,
    trend: (m.trend as 'positive' | 'negative' | 'neutral') ?? 'neutral',
  }));

  const chartData: FinancialChartDataPoint[] = backendData.trend.map((t) => ({
    period: t.period,
    value: t.revenue,
    formattedValue: t.revenue_formatted,
  }));

  const tableColumns: FinancialTableColumn[] = [
    { key: 'metric', header: 'Metric', align: 'left' },
    ...backendData.table.map((p) => ({
      key: `y${p.period}`,
      header: p.period,
      align: 'right' as const,
      isNumeric: true,
    })),
  ];

  const tableRows: FinancialTableRow[] = [
    {
      id: 'row-revenue',
      metric: 'Revenue',
      values: Object.fromEntries(
        backendData.table.map((p) => [`y${p.period}`, p.revenue_formatted])
      ),
      isHighlight: true,
    },
    {
      id: 'row-netincome',
      metric: 'Net Income',
      values: Object.fromEntries(
        backendData.table.map((p) => [`y${p.period}`, p.net_income_formatted])
      ),
      isHighlight: true,
    },
    {
      id: 'row-eps',
      metric: 'EPS',
      values: Object.fromEntries(
        backendData.table.map((p) => [`y${p.period}`, p.eps_formatted])
      ),
    },
    {
      id: 'row-opmargin',
      metric: 'Operating Margin',
      values: Object.fromEntries(
        backendData.table.map((p) => [`y${p.period}`, p.operating_margin_formatted])
      ),
      isHighlight: true,
    },
  ];

  const source: SourceCitationData = {
    sourceName: backendData.source.name,
    documentType: backendData.source.document_type ?? undefined,
    period: backendData.source.period ?? undefined,
  };

  const periodRange =
    backendData.trend.length > 0
      ? `${backendData.trend[0]?.period} – ${backendData.trend[backendData.trend.length - 1]?.period}`
      : '';

  return {
    title: `${backendData.company.name} (${backendData.company.ticker}) — Financial Overview`,
    subtitle: `Multi-Year Analysis · ${periodRange}`,
    narrative: backendData.summary,
    metrics,
    chart: {
      title: `Revenue Trend (${periodRange})`,
      subtitle: 'Annual reported revenue in billions USD',
      data: chartData,
      valueKey: 'value',
      unit: '$B',
    },
    table: {
      title: 'Financial Performance Summary',
      subtitle: 'Annual statement of operations summary',
      columns: tableColumns,
      rows: tableRows,
    },
    findings: backendData.findings.map((f) => f.text),
    source,
  };
}

/**
 * Maps question response visual artifacts (chart, table, metrics) into FinancialResponseData
 * if any visual artifacts were returned by the backend.
 */
export function mapBackendQuestionToFrontendVisuals(
  questionResponse: BackendFinancialQuestionResponse
): FinancialResponseData | undefined {
  const hasChart = Boolean(
    questionResponse.chart && questionResponse.chart.data && questionResponse.chart.data.length > 0
  );
  const hasTable = Boolean(
    questionResponse.table &&
      questionResponse.table.columns &&
      questionResponse.table.rows &&
      questionResponse.table.rows.length > 0
  );
  const hasMetrics = Boolean(questionResponse.metrics && questionResponse.metrics.length > 0);

  if (!hasChart && !hasTable && !hasMetrics) {
    return undefined;
  }

  const metrics: MetricItem[] | undefined = hasMetrics
    ? questionResponse.metrics!.map((m, idx) => ({
        id: `question-metric-${idx}`,
        label: m.name,
        value: m.value,
        change: m.change ?? undefined,
        changeLabel: m.change_label ?? undefined,
        period: m.period ?? undefined,
        trend: (m.trend as 'positive' | 'negative' | 'neutral') ?? 'neutral',
      }))
    : undefined;

  return {
    title:
      questionResponse.chart?.title ||
      questionResponse.table?.title ||
      `${questionResponse.company.name} (${questionResponse.company.ticker})`,
    subtitle: questionResponse.chart?.subtitle || questionResponse.table?.subtitle,
    metrics,
    chart: hasChart ? questionResponse.chart! : undefined,
    table: hasTable ? questionResponse.table! : undefined,
    source: {
      sourceName: questionResponse.source.name,
      documentType: questionResponse.source.document_type ?? undefined,
      period: questionResponse.source.period ?? undefined,
    },
  };
}

