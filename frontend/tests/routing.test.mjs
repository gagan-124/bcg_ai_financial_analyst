import assert from 'node:assert/strict';
import test from 'node:test';

function detectKnownCompany(input, preferActive) {
  const lower = input.toLowerCase();
  const companies = [];

  const teslaMatch = lower.search(/\b(tesla|teslas|tsla)('?s)?\b/i);
  if (teslaMatch !== -1) companies.push({ name: 'Tesla', index: teslaMatch });

  const msftMatch = lower.search(/\b(microsoft|microsofts|msft)('?s)?\b/i);
  if (msftMatch !== -1) companies.push({ name: 'Microsoft', index: msftMatch });

  const appleMatch = lower.search(/\b(apple|apples|aapl)('?s)?\b/i);
  if (appleMatch !== -1) companies.push({ name: 'Apple', index: appleMatch });

  if (companies.length === 0) return null;

  if (preferActive) {
    const activeLower = preferActive.toLowerCase();
    const activeMatch = companies.find((c) => activeLower.includes(c.name.toLowerCase()));
    if (activeMatch) return activeMatch.name;
  }

  companies.sort((a, b) => a.index - b.index);
  return companies[0].name;
}

function canonicalizeCompany(input) {
  if (!input) return null;
  return detectKnownCompany(input);
}

function extractCompany(input) {
  const detected = detectKnownCompany(input);
  if (detected) return detected;

  const cleaned = input
    .replace(/^(please\s+)?(analyze|show|compare|explain|give me|get)\s+/i, '')
    .replace(/(\s+financials?|\s+financial performance|\s+stock)?$/i, '')
    .trim();

  return cleaned || input.trim();
}

function isFinancialQuestion(content) {
  const trimmed = content.trim();
  const lower = trimmed.toLowerCase();

  if (
    /^(why|what|how|when|where|which|who|can|could|would|should|is|are|was|were|did|does|do|compare|explain|tell\s+me|describe)\b/i.test(
      trimmed
    )
  ) {
    return true;
  }

  if (trimmed.endsWith('?')) {
    return true;
  }

  if (
    /\b(why did|what caused|how did|what changed|what are|explain why|tell me why|tell me about|how come|compare\b)/i.test(
      lower
    )
  ) {
    return true;
  }

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

function isNewAnalysisRequest(content) {
  const trimmed = content.trim();

  if (isFinancialQuestion(trimmed)) {
    return false;
  }

  if (
    /^(apple|apples|apple's|aapl|microsoft|microsofts|microsoft's|msft|tesla|teslas|tesla's|tsla)$/i.test(
      trimmed.replace(/[!.,?]+$/, '')
    )
  ) {
    return true;
  }

  if (/^(please\s+)?(analyze|analyse)\s+/i.test(trimmed)) {
    return true;
  }

  if (
    /^(please\s+)?(show|give|display|provide|pull\s+up)(\s+me)?\s+(an?\s+)?(analysis|overview|financials?|financial\s+performance|financial\s+overview)\s+(of|for)\s+/i.test(
      trimmed
    )
  ) {
    return true;
  }

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

function classifyQueryIntent(content, activeCompany) {
  const trimmed = content.trim();
  const detectedCompany = detectKnownCompany(trimmed, activeCompany);
  const activeCanonical = canonicalizeCompany(activeCompany);

  if (isFinancialQuestion(trimmed)) {
    const targetCompany = detectedCompany || activeCanonical || 'Apple';
    return {
      intent: 'question',
      company: targetCompany,
    };
  }

  if (isNewAnalysisRequest(trimmed)) {
    const targetCompany = detectedCompany || activeCanonical || extractCompany(trimmed);
    return {
      intent: 'analysis',
      company: targetCompany,
    };
  }

  if (activeCanonical) {
    return {
      intent: 'question',
      company: detectedCompany || activeCanonical,
    };
  }

  if (detectedCompany) {
    return {
      intent: 'analysis',
      company: detectedCompany,
    };
  }

  return {
    intent: 'analysis',
    company: extractCompany(trimmed),
  };
}

// ----------------------------------------------------
// Acceptance Tests
// ----------------------------------------------------

test("Acceptance A: 'Analyze Apple' -> 'Why did Apple's net income increase over the years?'", () => {
  const step1 = classifyQueryIntent('Analyze Apple', undefined);
  assert.equal(step1.intent, 'analysis');
  assert.equal(step1.company, 'Apple');

  const step2WithApostrophe = classifyQueryIntent(
    "Why did Apple's net income increase over the years?",
    'Apple'
  );
  assert.equal(step2WithApostrophe.intent, 'question');
  assert.equal(step2WithApostrophe.company, 'Apple');

  // Without apostrophe: "apples"
  const step2NoApostrophe = classifyQueryIntent(
    'Why did apples net income increase over the years?',
    'Apple'
  );
  assert.equal(step2NoApostrophe.intent, 'question');
  assert.equal(step2NoApostrophe.company, 'Apple');
});

test("Acceptance B: 'Analyze Microsoft' -> 'Why did Microsoft's operating margin increase?'", () => {
  const step1 = classifyQueryIntent('Analyze Microsoft', undefined);
  assert.equal(step1.intent, 'analysis');
  assert.equal(step1.company, 'Microsoft');

  const step2 = classifyQueryIntent(
    "Why did Microsoft's operating margin increase?",
    'Microsoft'
  );
  assert.equal(step2.intent, 'question');
  assert.equal(step2.company, 'Microsoft');
});

test("Acceptance C: 'Analyze Microsoft' -> 'Compare Microsoft's revenue between 2024 and 2025.'", () => {
  const result = classifyQueryIntent(
    "Compare Microsoft's revenue between 2024 and 2025.",
    'Microsoft'
  );
  assert.equal(result.intent, 'question');
  assert.equal(result.company, 'Microsoft');
});

test("Acceptance D: 'Analyze Microsoft' -> 'Why did operating margin increase?' (no company name)", () => {
  const result = classifyQueryIntent(
    'Why did operating margin increase?',
    'Microsoft'
  );
  assert.equal(result.intent, 'question');
  assert.equal(result.company, 'Microsoft');
});

test("Acceptance E: 'Analyze Microsoft' -> 'Analyze Tesla' -> 'Why did profitability decline?'", () => {
  // Step 1: Microsoft
  const step1 = classifyQueryIntent('Analyze Microsoft', undefined);
  assert.equal(step1.intent, 'analysis');
  assert.equal(step1.company, 'Microsoft');

  // Step 2: Switch to Tesla
  const step2 = classifyQueryIntent('Analyze Tesla', 'Microsoft');
  assert.equal(step2.intent, 'analysis');
  assert.equal(step2.company, 'Tesla');

  // Step 3: Follow-up using new Tesla context
  const step3 = classifyQueryIntent('Why did profitability decline?', 'Tesla');
  assert.equal(step3.intent, 'question');
  assert.equal(step3.company, 'Tesla');
});

test("Acceptance F: 'Analyze Apple' -> 'What changed in Apple's operating margin?'", () => {
  const step1 = classifyQueryIntent('Analyze Apple', undefined);
  assert.equal(step1.intent, 'analysis');
  assert.equal(step1.company, 'Apple');

  const step2 = classifyQueryIntent(
    "What changed in Apple's operating margin?",
    'Apple'
  );
  assert.equal(step2.intent, 'question');
  assert.equal(step2.company, 'Apple');
});

test('Additional Edge Cases: Analysis phrasing variants', () => {
  const t1 = classifyQueryIntent("Analyze Apple's financial performance", undefined);
  assert.equal(t1.intent, 'analysis');
  assert.equal(t1.company, 'Apple');

  const t2 = classifyQueryIntent('Give me an analysis of Apple', undefined);
  assert.equal(t2.intent, 'analysis');
  assert.equal(t2.company, 'Apple');

  const t3 = classifyQueryIntent("Show me Apple's financials", undefined);
  assert.equal(t3.intent, 'analysis');
  assert.equal(t3.company, 'Apple');

  const t4 = classifyQueryIntent('Show Apple financials', undefined);
  assert.equal(t4.intent, 'analysis');
  assert.equal(t4.company, 'Apple');

  const t5 = classifyQueryIntent('Give me an overview of Microsoft', undefined);
  assert.equal(t5.intent, 'analysis');
  assert.equal(t5.company, 'Microsoft');
});

test('Additional Edge Cases: Question phrasing variants', () => {
  const q1 = classifyQueryIntent('Why did Apple revenue grow?', 'Apple');
  assert.equal(q1.intent, 'question');
  assert.equal(q1.company, 'Apple');

  const q2 = classifyQueryIntent('Compare Apple and Microsoft revenue', 'Apple');
  assert.equal(q2.intent, 'question');
  assert.equal(q2.company, 'Apple');

  const q3 = classifyQueryIntent("What caused Tesla's profitability to decline?", 'Microsoft');
  assert.equal(q3.intent, 'question');
  assert.equal(q3.company, 'Tesla'); // Explicitly names Tesla in question
});
