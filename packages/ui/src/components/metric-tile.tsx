interface MetricTileProps {
  value: string | number | null;
  label: string;
}

export function MetricTile({ value, label }: MetricTileProps) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-800/40">
      <div className="text-2xl font-bold tabular-nums text-orange-700 dark:text-orange-400">
        {value ?? '-'}
      </div>
      <div className="mt-1 text-[11px] font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        {label}
      </div>
    </div>
  );
}
