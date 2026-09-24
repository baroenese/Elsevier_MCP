import type { Metadata } from 'next';
import './globals.css';
import { NavShell } from './nav-shell';

export const metadata: Metadata = {
  title: 'Elsevier Academic Explorer',
  description:
    'Scopus search, research trends, and journal metrics powered by the Elsevier MCP server',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-dvh bg-zinc-50 font-sans text-zinc-800 antialiased dark:bg-zinc-950 dark:text-zinc-200">
        <NavShell>{children}</NavShell>
      </body>
    </html>
  );
}
