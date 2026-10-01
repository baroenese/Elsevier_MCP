'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

const navLinks = [
  { href: '/search', label: 'Search' },
  { href: '/trends', label: 'Trends' },
  { href: '/journals', label: 'Journals' },
  { href: '/institutions', label: 'Institutions' },
  { href: '/settings', label: 'Settings' },
];

export function NavShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [healthBadge, setHealthBadge] = useState<{
    text: string;
    ok: boolean;
  }>({ text: 'Checking...', ok: false });

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => {
        if (data.api_key_set) {
          setHealthBadge({
            text: `API key: ${data.api_key_source}`,
            ok: true,
          });
        } else {
          setHealthBadge({ text: 'No API key. Open Settings.', ok: false });
        }
      })
      .catch(() => setHealthBadge({ text: 'Connection error', ok: false }));
  }, []);

  return (
    <>
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-600 text-lg font-bold text-white dark:bg-orange-500">
              E
            </div>
            <div>
              <h1 className="text-[15px] font-semibold text-zinc-900 dark:text-zinc-100">
                Elsevier Academic Explorer
              </h1>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Scopus search, trends, and journal metrics
              </p>
            </div>
          </div>
          <div
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              healthBadge.ok
                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-400'
                : 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400'
            }`}
          >
            {healthBadge.text}
          </div>
        </div>
      </header>

      <nav
        className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
        role="tablist"
      >
        <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 sm:px-6">
          {navLinks.map((link) => {
            const isActive = pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                role="tab"
                className={`border-b-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap ${
                  isActive
                    ? 'border-orange-600 text-zinc-900 dark:border-orange-500 dark:text-zinc-100'
                    : 'border-transparent text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">{children}</main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 text-xs text-zinc-500 sm:px-6 dark:text-zinc-400">
        The stdio MCP server (
        <code className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          elsevier-mcp-server
        </code>
        ) remains available for AI clients.
      </footer>
    </>
  );
}
