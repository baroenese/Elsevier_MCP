'use client';

import { useState } from 'react';
import { api, fmt } from '@/lib/api-client';
import type { Paper, SearchResult } from '@/lib/api-client';
import { SkeletonRows, StatusText } from '@elsevier-mcp/ui';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [author, setAuthor] = useState('');
  const [year, setYear] = useState('');
  const [openAccess, setOpenAccess] = useState(false);
  const [count, setCount] = useState('25');

  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [isError, setIsError] = useState(false);
  const [results, setResults] = useState<SearchResult | null>(null);

  const [abstractData, setAbstractData] = useState<{
    title: string;
    authors: string;
    journal: string;
    year: string;
    citations: string;
    doi: string;
    abstract: string;
  } | null>(null);
  const [loadingAbstract, setLoadingAbstract] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setStatusMsg('Searching...');
    setIsError(false);
    setResults(null);
    try {
      const data = await api.search({
        query,
        author: author || null,
        year: year || null,
        open_access: openAccess,
        count: parseInt(count),
      });
      if (!data.success) {
        setStatusMsg(data.error ?? 'Search failed');
        setIsError(true);
        return;
      }
      setStatusMsg('Done.');
      setResults(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An error occurred';
      setStatusMsg(msg);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  const openAbstractModal = async (eid: string, doi: string) => {
    if (!eid && !doi) return;
    setLoadingAbstract(true);
    try {
      const data = await api.abstract({ eid: eid || null, doi: doi || null });
      if (!data.success || !data.paper) {
        setAbstractData({
          title: 'Error',
          authors: '',
          journal: '',
          year: '',
          citations: '0',
          doi: '',
          abstract: data.error ?? 'Failed to load abstract.',
        });
      } else {
        const p = data.paper;
        let authorsStr = 'Unknown';
        const rawAuthors: unknown = p.authors;
        if (typeof rawAuthors === 'string') {
          authorsStr = rawAuthors;
        } else if (Array.isArray(rawAuthors)) {
          authorsStr = (rawAuthors as unknown[]).join(', ');
        } else if (typeof rawAuthors === 'object' && rawAuthors !== null) {
          const authObj = rawAuthors as Record<string, unknown>;
          if (Array.isArray(authObj.author)) {
            authorsStr = authObj.author
              .map((a: Record<string, unknown>) => {
                const pref = a['preferred-name'] as Record<string, unknown> | undefined;
                return (
                  pref?.['ce:indexed-name'] ||
                  a['ce:indexed-name'] ||
                  `${a['ce:surname'] ?? ''} ${a['ce:given-name'] ?? ''}`.trim() ||
                  'Unknown'
                );
              })
              .join(', ');
          }
        }

        setAbstractData({
          title: p.title,
          authors: authorsStr,
          journal: p.journal,
          year: String(p.year ?? '').slice(0, 4),
          citations: String(p.citations ?? 0),
          doi: p.doi,
          abstract:
            ((p as unknown as Record<string, unknown>).abstract as string) ??
            'No abstract available.',
        });
      }
    } catch {
      setAbstractData({
        title: 'Error',
        authors: '',
        journal: '',
        year: '',
        citations: '0',
        doi: '',
        abstract: 'Failed to load abstract.',
      });
    } finally {
      setLoadingAbstract(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Form */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <form onSubmit={handleSearch}>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="sm:col-span-2">
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                Query
              </span>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
                placeholder="machine learning for drug discovery"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                Author (optional)
              </span>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="e.g. Hinton"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                Year (optional)
              </span>
              <input
                type="text"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                placeholder="2024"
                pattern="\d{4}"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
            <label className="flex items-center gap-2 pt-6 text-sm text-zinc-700 dark:text-zinc-300">
              <input
                type="checkbox"
                checked={openAccess}
                onChange={(e) => setOpenAccess(e.target.checked)}
                className="h-4 w-4 rounded border-zinc-300 accent-orange-600"
              />
              Open access only
            </label>
            <label>
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                Results
              </span>
              <select
                value={count}
                onChange={(e) => setCount(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              >
                <option value="10">10</option>
                <option value="25">25</option>
              </select>
            </label>
            <div className="flex items-center gap-3 sm:col-span-2">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-700 active:scale-[0.98] disabled:cursor-wait disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                {loading ? 'Searching...' : 'Search Scopus'}
              </button>
              {statusMsg && <StatusText message={statusMsg} isError={isError} />}
            </div>
          </div>
        </form>
      </div>

      {/* Summary */}
      {results?.success && (
        <p className="text-[13px] text-zinc-500 dark:text-zinc-400">
          <strong className="text-zinc-900 dark:text-zinc-100">
            {fmt(results.total_results)}
          </strong>{' '}
          papers found, showing top {results.papers?.length ?? 0} by citations.
          Query: <code className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">{results.query}</code>
        </p>
      )}

      {/* Results Table */}
      <div className="rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900 overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr>
              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 w-8">#</th>
              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Title</th>
              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Authors</th>
              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Journal</th>
              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 w-14">Year</th>
              <th className="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 w-20">Citations</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <SkeletonRows cols={6} rows={5} />
            ) : results?.papers && results.papers.length > 0 ? (
              results.papers.map((p: Paper, i: number) => (
                <tr
                  key={p.eid || p.doi || i}
                  onClick={() => openAbstractModal(p.eid, p.doi)}
                  className="cursor-pointer border-t border-zinc-100 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800/50"
                >
                  <td className="px-3 py-2.5 align-top text-[13.5px] tabular-nums text-zinc-500">{i + 1}</td>
                  <td className="px-3 py-2.5 align-top text-[13.5px] max-w-[320px] font-medium text-zinc-900 dark:text-zinc-100">{p.title}</td>
                  <td className="px-3 py-2.5 align-top text-[13.5px] text-zinc-600 dark:text-zinc-400">{p.authors}</td>
                  <td className="px-3 py-2.5 align-top text-[13.5px] text-zinc-600 dark:text-zinc-400">{p.journal}</td>
                  <td className="px-3 py-2.5 align-top text-[13.5px] tabular-nums">{String(p.year ?? '').slice(0, 4)}</td>
                  <td className="px-3 py-2.5 align-top text-[13.5px] tabular-nums text-right">{fmt(p.citations)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-14 text-center">
                  <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    {results?.papers?.length === 0 ? 'No results found' : 'No results yet'}
                  </p>
                  <p className="mt-1 text-[13px] text-zinc-500 dark:text-zinc-400">
                    Run a search above. Click any row to open its abstract.
                  </p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Abstract Modal */}
      {(abstractData || loadingAbstract) && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto bg-zinc-950/60 p-4 sm:p-8"
          onClick={(e) => { if (e.target === e.currentTarget) setAbstractData(null); }}
        >
          <div className="relative mx-auto max-w-2xl rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <button
              onClick={() => setAbstractData(null)}
              className="absolute right-3 top-2 text-2xl leading-none text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
              aria-label="Close"
            >
              &times;
            </button>
            {loadingAbstract ? (
              <div className="space-y-3">
                <div className="h-6 w-3/4 rounded bg-zinc-200 animate-pulse dark:bg-zinc-800" />
                <div className="h-4 w-1/2 rounded bg-zinc-200 animate-pulse dark:bg-zinc-800" />
                <div className="h-4 w-full rounded bg-zinc-200 animate-pulse dark:bg-zinc-800" />
                <div className="h-4 w-5/6 rounded bg-zinc-200 animate-pulse dark:bg-zinc-800" />
              </div>
            ) : abstractData ? (
              <>
                <h2 className="mr-8 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  {abstractData.title}
                </h2>
                <p className="mt-1 mb-4 text-[13px] text-zinc-500 dark:text-zinc-400">
                  {abstractData.authors}. {abstractData.journal}, {abstractData.year}.{' '}
                  {fmt(abstractData.citations)} citations.
                  {abstractData.doi && (
                    <>
                      {' '}
                      <a
                        href={`https://doi.org/${abstractData.doi}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-orange-700 hover:underline dark:text-orange-400"
                      >
                        doi.org/{abstractData.doi}
                      </a>
                    </>
                  )}
                </p>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {abstractData.abstract}
                </p>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
