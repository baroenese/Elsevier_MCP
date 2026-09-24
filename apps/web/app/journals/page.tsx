'use client';

import { useState } from 'react';
import { api } from '@/lib/api-client';
import type { JournalMetrics } from '@/lib/api-client';
import { MetricTile, QuartileBadge, StatusText } from '@elsevier-mcp/ui';

export default function JournalsPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [isError, setIsError] = useState(false);
  const [journal, setJournal] = useState<JournalMetrics | null>(null);

  const [compareList, setCompareList] = useState<string[]>([]);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResults, setCompareResults] = useState<JournalMetrics[]>([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setStatusMsg('Fetching metrics...');
    setIsError(false);
    setJournal(null);

    try {
      const data = await api.journalMetrics(query.trim());
      if (!data.success || !data.journal) {
        setStatusMsg(data.error ?? 'Journal not found');
        setIsError(true);
        return;
      }
      setStatusMsg('Done.');
      setJournal(data.journal);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error fetching metrics';
      setStatusMsg(msg);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  const addToCompare = (title: string) => {
    const trimmed = title.trim();
    if (trimmed && !compareList.includes(trimmed) && compareList.length < 4) {
      setCompareList([...compareList, trimmed]);
    }
  };

  const removeFromCompare = (title: string) => {
    setCompareList(compareList.filter((t) => t !== title));
  };

  const handleCompare = async () => {
    if (compareList.length < 1) return;
    setCompareLoading(true);
    setStatusMsg('Comparing...');
    setIsError(false);

    try {
      const data = await api.journalCompare(compareList);
      if (!data.success || !data.journals) {
        setStatusMsg(data.error ?? 'Comparison failed');
        setIsError(true);
        return;
      }
      const valid = data.journals
        .filter((j: { success: boolean; journal?: JournalMetrics }) => Boolean(j.success && j.journal))
        .map((j: { success: boolean; journal?: JournalMetrics }) => j.journal as JournalMetrics);
      setCompareResults(valid);
      setStatusMsg('Done.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Comparison failed';
      setStatusMsg(msg);
      setIsError(true);
    } finally {
      setCompareLoading(false);
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
                Journal title or ISSN
              </span>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                required
                placeholder="e.g. Nature, or 0028-0836"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading}
                className="w-full inline-flex justify-center items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-700 active:scale-[0.98] disabled:cursor-wait disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                {loading ? 'Fetching...' : 'Get metrics'}
              </button>
            </div>
            <div className="flex items-end">
              <button
                type="button"
                onClick={() => query.trim() && addToCompare(query.trim())}
                className="w-full inline-flex justify-center items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold text-zinc-700 transition-colors hover:bg-zinc-100 active:scale-[0.98] dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
              >
                Add to compare
              </button>
            </div>
            <div className="flex flex-wrap items-center gap-3 sm:col-span-2 lg:col-span-4">
              <button
                type="button"
                onClick={handleCompare}
                disabled={compareList.length === 0 || compareLoading}
                className="inline-flex items-center gap-2 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-200 disabled:opacity-50 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700"
              >
                {compareLoading ? 'Comparing...' : 'Compare selected'}
              </button>
              {statusMsg && <StatusText message={statusMsg} isError={isError} />}
            </div>
          </div>
        </form>
      </div>

      {/* Compare Chips */}
      {compareList.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {compareList.map((item) => (
            <span
              key={item}
              className="inline-flex items-center gap-2 rounded-full bg-zinc-100 px-3 py-1 text-[13px] text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
            >
              {item}
              <button
                type="button"
                onClick={() => removeFromCompare(item)}
                className="text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 text-sm leading-none"
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Single Journal Result Card */}
      {journal && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-[17px] font-semibold text-zinc-900 dark:text-zinc-100">
                {journal.title}
              </h3>
              <p className="mt-0.5 text-[13px] text-zinc-500 dark:text-zinc-400">
                {[
                  journal.publisher,
                  journal.issn ? `ISSN ${journal.issn}` : null,
                  journal.eissn ? `eISSN ${journal.eissn}` : null,
                  journal.open_access ? 'Open Access' : null,
                ]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            </div>
            <button
              onClick={() => addToCompare(journal.title)}
              className="text-xs font-semibold text-orange-600 hover:underline dark:text-orange-400"
            >
              + Add to compare
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <MetricTile
              value={journal.citescore?.current}
              label={`CiteScore ${journal.citescore?.year ?? ''}`}
            />
            <MetricTile
              value={journal.citescore?.tracker}
              label={`Tracker ${journal.citescore?.tracker_year ?? ''}`}
            />
            <MetricTile
              value={journal.sjr?.value}
              label={`SJR ${journal.sjr?.year ?? ''}`}
            />
            <MetricTile
              value={journal.snip?.value}
              label={`SNIP ${journal.snip?.year ?? ''}`}
            />
            <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-800/40">
              <div className="text-2xl font-bold">
                <QuartileBadge quartile={journal.best_quartile} />
              </div>
              <div className="mt-1 text-[11px] font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Best quartile
              </div>
            </div>
          </div>

          {/* Subject Rankings */}
          {journal.subject_rankings && journal.subject_rankings.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Subject Rankings
              </h4>
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                      Subject Code
                    </th>
                    <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                      Rank
                    </th>
                    <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                      Percentile
                    </th>
                    <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                      Quartile
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {journal.subject_rankings.map(
                    (
                      r: {
                        subject_code: string;
                        rank: number;
                        percentile: number;
                        quartile: string;
                      },
                      i: number
                    ) => (
                    <tr
                      key={i}
                      className="border-t border-zinc-100 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800/50"
                    >
                      <td className="px-3 py-2 font-mono text-xs">{r.subject_code}</td>
                      <td className="px-3 py-2 tabular-nums">#{r.rank}</td>
                      <td className="px-3 py-2 tabular-nums">{r.percentile}%</td>
                      <td className="px-3 py-2">
                        <QuartileBadge quartile={r.quartile} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Comparison Results */}
      {compareResults.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-[15px] font-semibold text-zinc-900 dark:text-zinc-100">
            Journal Comparison
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {compareResults.map((j) => (
              <div
                key={j.title}
                className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 space-y-3"
              >
                <div>
                  <h4 className="text-[15px] font-semibold text-zinc-900 dark:text-zinc-100">
                    {j.title}
                  </h4>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {[j.publisher, j.issn ? `ISSN ${j.issn}` : null].filter(Boolean).join(' · ')}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <MetricTile value={j.citescore?.current} label="CiteScore" />
                  <MetricTile value={j.sjr?.value} label="SJR" />
                  <MetricTile value={j.snip?.value} label="SNIP" />
                  <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-800/40">
                    <div className="text-2xl font-bold">
                      <QuartileBadge quartile={j.best_quartile} />
                    </div>
                    <div className="mt-1 text-[11px] font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                      Quartile
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
