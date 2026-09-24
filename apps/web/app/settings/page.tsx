'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api-client';
import type { HealthResult, ToolDef } from '@/lib/api-client';
import { StatusText } from '@elsevier-mcp/ui';

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState('');
  const [instToken, setInstToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<HealthResult | null>(null);
  const [statusMsg, setStatusMsg] = useState('');
  const [isError, setIsError] = useState(false);
  const [tools, setTools] = useState<ToolDef[]>([]);

  const loadStatus = async () => {
    try {
      const data = await api.health();
      setStatus(data);
      const toolsData = await api.tools();
      setTools(toolsData.tools || []);
    } catch {
      setStatusMsg('Failed to load status');
      setIsError(true);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim() && !instToken.trim()) {
      setStatusMsg('Nothing to save. Enter a key first.');
      setIsError(true);
      return;
    }
    setLoading(true);
    setStatusMsg('Saving...');
    setIsError(false);

    try {
      const res = await api.config({
        api_key: apiKey.trim() || undefined,
        insttoken: instToken.trim() || undefined,
      });
      if (!res.success) {
        setStatusMsg('Failed to save credentials');
        setIsError(true);
        return;
      }
      setStatusMsg('Saved credentials.');
      setApiKey('');
      setInstToken('');
      setStatus(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Save failed';
      setStatusMsg(msg);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    setLoading(true);
    setStatusMsg('Clearing...');
    setIsError(false);
    try {
      const res = await api.config({ api_key: '', insttoken: '' });
      setStatusMsg('Saved credentials cleared.');
      setStatus(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Clear failed';
      setStatusMsg(msg);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* Credentials Card */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="mb-1 text-[15px] font-semibold text-zinc-900 dark:text-zinc-100">
          Elsevier API credentials
        </h2>
        <p className="text-[13px] text-zinc-500 dark:text-zinc-400 mb-4">
          Credentials are stored in{' '}
          <code className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
            {status?.config_file || '~/.elsevier-mcp/config.json'}
          </code>{' '}
          with 0600 permissions. Shell-exported variables take precedence.
        </p>

        <form onSubmit={handleSave}>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                API key
              </span>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={status?.api_key_set ? '•••••••••••••••• (Active)' : 'Paste API key to configure'}
                autoComplete="off"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-[13px] font-medium text-zinc-600 dark:text-zinc-400">
                Institutional token (optional)
              </span>
              <input
                type="password"
                value={instToken}
                onChange={(e) => setInstToken(e.target.value)}
                placeholder={status?.insttoken_set ? '•••••••••••••••• (Active)' : 'Paste token to configure'}
                autoComplete="off"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-500 focus:border-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-600/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
              />
            </label>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-700 active:scale-[0.98] disabled:cursor-wait disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
            >
              Save credentials
            </button>
            <button
              type="button"
              onClick={handleClear}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold text-zinc-700 transition-colors hover:bg-zinc-100 active:scale-[0.98] dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
            >
              Clear saved
            </button>
            {statusMsg && <StatusText message={statusMsg} isError={isError} />}
          </div>
        </form>
      </div>

      {/* Status Panel */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h3 className="mb-3 text-[15px] font-semibold text-zinc-900 dark:text-zinc-100">
          Status
        </h3>
        <dl className="grid gap-x-6 gap-y-2 text-[13.5px] sm:grid-cols-[200px_1fr]">
          <dt className="text-zinc-500 dark:text-zinc-400">Server version</dt>
          <dd className="font-medium text-zinc-900 dark:text-zinc-100">{status?.version || '2.0.0'}</dd>

          <dt className="text-zinc-500 dark:text-zinc-400">API key configured</dt>
          <dd>
            {status?.api_key_set ? (
              <span className="text-emerald-700 dark:text-emerald-400 font-medium">
                yes ({status.api_key_source})
              </span>
            ) : (
              <span className="text-red-600 dark:text-red-400 font-medium">no</span>
            )}
          </dd>

          <dt className="text-zinc-500 dark:text-zinc-400">Institutional token</dt>
          <dd>{status?.insttoken_set ? 'yes' : 'no'}</dd>

          <dt className="text-zinc-500 dark:text-zinc-400">Config file</dt>
          <dd className="font-mono text-xs">{status?.config_file || 'Unknown'}</dd>

          <dt className="text-zinc-500 dark:text-zinc-400">MCP stdio server</dt>
          <dd className="text-zinc-600 dark:text-zinc-400">
            <code className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
              elsevier-mcp-server
            </code>{' '}
            active on stdio for AI clients
          </dd>
        </dl>
      </div>

      {/* Registered Tools */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h3 className="mb-1 text-[15px] font-semibold text-zinc-900 dark:text-zinc-100">
          Registered MCP tools ({tools.length})
        </h3>
        <p className="text-[13px] text-zinc-500 dark:text-zinc-400 mb-3">
          These tools are exposed over JSON-RPC 2.0 stdio and reused by this UI.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                  Tool
                </th>
                <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                  Description
                </th>
              </tr>
            </thead>
            <tbody>
              {tools.map((t) => (
                <tr
                  key={t.name}
                  className="border-t border-zinc-100 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800/50"
                >
                  <td className="px-3 py-2 whitespace-nowrap font-mono text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                    {t.name}
                  </td>
                  <td className="px-3 py-2 text-zinc-600 dark:text-zinc-400 text-xs">
                    {t.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
