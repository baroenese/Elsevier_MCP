'use client';

import { useState } from 'react';
import { api, fmt } from '@/lib/api-client';
import type { InstitutionResult } from '@/lib/api-client';
import { MetricTile, SkeletonRows, StatusText } from '@elsevier-mcp/ui';

export default function InstitutionsPage() {
  const [institution, setInstitution] = useState('');
  const [year, setYear] = useState('2024');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [isError, setIsError] = useState(false);
  const [results, setResults] = useState<InstitutionResult | null>(null);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!institution.trim()) return;
    setLoading(true);
    setStatusMsg('Analyzing...');
    setIsError(false);
    setResults(null);
    try {
      const data = await api.institution({
        institution,
        year: parseInt(year) || new Date().getFullYear(),
      });
      if (!data.success) {
        setStatusMsg(data.error ?? 'Lookup failed');
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

  const inputClass =
    'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100';

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <form onSubmit={handleLookup}>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="sm:col-span-2">
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                Institution name
              </span>
              <input
                type="text"
                value={institution}
                onChange={(e) => setInstitution(e.target.value)}
                required
                placeholder='e.g. "Universitas Indonesia"'
                className={inputClass}
              />
            </label>
            <label>
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                Year
              </span>
              <input
                type="text"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                pattern="\d{4}"
                placeholder={String(new Date().getFullYear())}
                className={inputClass}
              />
            </label>
            <div className="flex items-center gap-3 lg:justify-end">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-700 active:scale-[0.98] disabled:cursor-wait disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                {loading ? 'Analyzing...' : 'Analyze institution'}
              </button>
            </div>
          </div>
          <div className="mt-3">{statusMsg && <StatusText message={statusMsg} isError={isError} />}</div>
        </form>
      </div>

      {results?.success && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <MetricTile value={fmt(results.total_papers ?? 0)} label="Papers (Scopus)" />
            <MetricTile value={results.year ?? '-'} label="Publication year" />
            <MetricTile
              value={String(results.institution ?? '')}
              label="Institution queried"
            />
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 w-8">#</th>
                  <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Top cited papers</th>
                  <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Authors</th>
                  <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Journal</th>
                  <th className="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 w-20">Citations</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <SkeletonRows cols={5} rows={5} />
                ) : results.top_papers && results.top_papers.length > 0 ? (
                  results.top_papers.map((p, i) => (
                    <tr
                      key={p.doi || i}
                      className="border-t border-zinc-100 dark:border-zinc-800"
                    >
                      <td className="px-3 py-2.5 align-top text-[13.5px] tabular-nums text-zinc-500">{i + 1}</td>
                      <td className="px-3 py-2.5 align-top text-[13.5px] max-w-[380px] font-medium text-zinc-900 dark:text-zinc-100">{p.title}</td>
                      <td className="px-3 py-2.5 align-top text-[13.5px] text-zinc-600 dark:text-zinc-400">{p.authors}</td>
                      <td className="px-3 py-2.5 align-top text-[13.5px] text-zinc-600 dark:text-zinc-400">{p.journal}</td>
                      <td className="px-3 py-2.5 align-top text-[13.5px] tabular-nums text-right">{fmt(p.citations)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-14 text-center">
                      <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">No papers found</p>
                      <p className="mt-1 text-[13px] text-zinc-500 dark:text-zinc-400">
                        Try a different institution name or year.
                      </p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
