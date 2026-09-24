interface QuartileBadgeProps {
  quartile: string | null;
}

export function QuartileBadge({ quartile }: QuartileBadgeProps) {
  const q = (quartile ?? '').toLowerCase();
  const isQ1 = q === 'q1';
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold ${
      isQ1
        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-400'
        : 'bg-orange-100 text-orange-800 dark:bg-orange-500/15 dark:text-orange-400'
    }`}>
      {quartile || '-'}
    </span>
  );
}
