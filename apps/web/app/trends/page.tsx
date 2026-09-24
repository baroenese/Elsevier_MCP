'use client';

import { useState } from 'react';
import { api, fmt } from '@/lib/api-client';
import type { TrendsResult } from '@/lib/api-client';
import { StatusText, SkeletonRows } from '@elsevier-mcp/ui';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function TrendsPage() {
  const [field, setField] = useState('');
  const [startYear, setStartYear] = useState('2020');
  const [endYear, setEndYear] = useState('2024');

  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [isError, setIsError] = useState(false);
  const [data, setData] = useState<TrendsResult | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!field.trim()) return;
    setLoading(true);
    setStatusMsg('Analyzing...');
    setIsError(false);
    setData(null);

    try {
      const res = await api.trends({
        field: field.trim(),
        start_year: parseInt(startYear, 10),
        end_year: parseInt(endYear, 10),
      });
      if (!res.success) {
        setStatusMsg(res.error ?? 'Trend analysis failed');
        setIsError(true);
        return;
      }
      setStatusMsg('Done.');
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An error occurred';
      setStatusMsg(msg);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  const years = data?.yearly_papers ? Object.keys(data.yearly_papers).sort() : [];
  const chartData = years.map((y) => ({
    year: y,
    papers: data?.yearly_papers?.[y] ?? 0,
  }));

  return (
    <div className="space-y-4">
      {/* Form */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <form onSubmit={handleSearch}>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="sm:col-span-2">
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                Research field
              </span>
              <input
                type="text"
                value={field}
                onChange={(e) => setField(e.target.value)}
                required
                placeholder="e.g. quantum computing"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                From year
              </span>
              <input
                type="number"
                value={startYear}
                onChange={(e) => setStartYear(e.target.value)}
                min="1970"
                max="2026"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                To year
              </span>
              <input
                type="number"
                value={endYear}
                onChange={(e) => setEndYear(e.target.value)}
                min="1970"
                max="2026"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
            <div className="flex items-center gap-3 sm:col-span-2 lg:col-span-4">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-700 active:scale-[0.98] disabled:cursor-wait disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                {loading ? 'Analyzing...' : 'Analyze trends'}
              </button>
              {statusMsg && <StatusText message={statusMsg} isError={isError} />}
            </div>
          </div>
        </form>
      </div>

      {/* Summary */}
      {data?.success && (
        <p className="text-[13px] text-zinc-500 dark:text-zinc-400">
          <strong className="text-zinc-900 dark:text-zinc-100">
            {fmt(data.total_papers)}
          </strong>{' '}
          papers on <em>{data.field}</em> across {years.length} years.
        </p>
      )}

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-4 sm:p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h3 className="mb-3 text-[14px] font-semibold text-zinc-900 dark:text-zinc-100">
            Publications per year
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#71717a" opacity={0.2} />
                <XAxis dataKey="year" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#18181b',
                    borderColor: '#27272a',
                    borderRadius: '8px',
                    color: '#f4f4f5',
                  }}
                  itemStyle={{ color: '#ea580c' }}
                />
                <Line
                  type="monotone"
                  dataKey="papers"
                  name="Papers"
                  stroke="#ea580c"
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#ea580c' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900 overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr>
              <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Year
              </th>
              <th className="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Papers
              </th>
              <th className="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Growth
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <SkeletonRows cols={3} rows={4} />
            ) : years.length > 0 ? (
              years.map((y, i) => {
                const growthKey = i > 0 ? `${years[i - 1]}-${y}` : null;
                const growth = growthKey && data?.growth_rates ? data.growth_rates[growthKey] : null;
                return (
                  <tr
                    key={y}
                    className="border-t border-zinc-100 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800/50"
                  >
                    <td className="px-3 py-2.5 tabular-nums text-zinc-700 dark:text-zinc-300 font-medium">
                      {y}
                    </td>
                    <td className="px-3 py-2.5 tabular-nums text-right font-medium text-zinc-900 dark:text-zinc-100">
                      {fmt(data?.yearly_papers?.[y])}
                    </td>
                    <td className="px-3 py-2.5 tabular-nums text-right">
                      {growth !== null && growth !== undefined ? (
                        <span
                          className={`font-medium ${
                            growth >= 0
                              ? 'text-emerald-700 dark:text-emerald-400'
                              : 'text-red-600 dark:text-red-400'
                          }`}
                        >
                          {growth >= 0 ? '+' : ''}
                          {growth}%
                        </span>
                      ) : (
                        <span className="text-zinc-400">-</span>
                      )}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={3} className="py-14 text-center">
                  <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    No trend data yet
                  </p>
                  <p className="mt-1 text-[13px] text-zinc-500 dark:text-zinc-400">
                    Enter a research field above to plot publication counts per year.
                  </p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
