/* Typed fetch wrapper for BFF Route Handlers. */

export interface Paper {
  title: string;
  authors: string;
  journal: string;
  year: string;
  citations: number;
  doi: string;
  eid: string;
  open_access?: boolean;
}

export interface SearchResult {
  success: boolean;
  total_results?: number;
  start?: number;
  papers?: Paper[];
  query?: string;
  error?: string;
}

export interface TrendsResult {
  success: boolean;
  field?: string;
  yearly_papers?: Record<string, number>;
  growth_rates?: Record<string, number>;
  total_papers?: number;
  error?: string;
}

export interface JournalMetrics {
  title: string;
  publisher: string;
  issn: string;
  eissn: string;
  open_access: boolean;
  best_quartile: string | null;
  citescore: {
    current: number | null;
    year: string | null;
    tracker: number | null;
    tracker_year: string | null;
  };
  sjr: { value: number | null; year: string | null };
  snip: { value: number | null; year: string | null };
  subject_rankings: Array<{
    subject_code: string;
    rank: number;
    percentile: number;
    quartile: string;
  }>;
}

export interface JournalResult {
  success: boolean;
  journal?: JournalMetrics;
  error?: string;
}

export interface JournalCompareResult {
  success: boolean;
  journals?: Array<{ query: string; success: boolean; journal?: JournalMetrics; error?: string }>;
  error?: string;
}

export interface InstitutionResult {
  success: boolean;
  institution?: string;
  year?: number;
  total_papers?: number;
  top_papers?: Array<{
    title: string;
    authors: string;
    journal: string;
    citations: number;
    doi: string;
  }>;
  error?: string;
}

export interface AuthorPapersResult {
  success: boolean;
  total_results?: number;
  start?: number;
  author_id?: string | null;
  author_name?: string | null;
  papers?: Paper[];
  query?: string;
  error?: string;
}

export interface HealthResult {
  success: boolean;
  version: string;
  api_key_set: boolean;
  api_key_source: string;
  insttoken_set: boolean;
  config_file: string;
}

export interface ToolDef {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  return res.json() as Promise<T>;
}

const jsonPost = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

export const api = {
  search: (body: {
    query: string;
    author?: string | null;
    year?: string | null;
    open_access?: boolean;
    count?: number;
    start?: number;
  }) => apiFetch<SearchResult>('/api/search', jsonPost(body)),

  abstract: (body: { eid?: string | null; doi?: string | null }) =>
    apiFetch<{ success: boolean; paper?: Paper; error?: string }>(
      '/api/abstract',
      jsonPost(body),
    ),

  trends: (body: { field: string; start_year: number; end_year: number }) =>
    apiFetch<TrendsResult>('/api/trends', jsonPost(body)),

  journalMetrics: (query: string) => {
    const isIssn =
      query.replace(/-/g, '').length === 8 && !query.includes(' ');
    const param = isIssn
      ? `issn=${encodeURIComponent(query)}`
      : `query=${encodeURIComponent(query)}`;
    return apiFetch<JournalResult>(`/api/journal-metrics?${param}`);
  },

  journalCompare: (queries: string[]) =>
    apiFetch<JournalCompareResult>(
      '/api/journal-compare',
      jsonPost({ queries }),
    ),

  institution: (body: { institution: string; year?: number }) =>
    apiFetch<InstitutionResult>('/api/institution', jsonPost(body)),

  authorPapers: (body: {
    author_id?: string | null;
    author_name?: string | null;
    affiliation?: string | null;
    year?: string | null;
    count?: number;
    start?: number;
  }) => apiFetch<AuthorPapersResult>('/api/author-papers', jsonPost(body)),

  health: () => apiFetch<HealthResult>('/api/health'),

  config: (body: { api_key?: string; insttoken?: string }) =>
    apiFetch<HealthResult>('/api/config', jsonPost(body)),

  tools: () =>
    apiFetch<{ success: boolean; tools: ToolDef[] }>('/api/tools'),
};

export function fmt(n: number | string | null | undefined): string {
  return Number(n ?? 0).toLocaleString();
}
