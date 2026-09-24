interface SkeletonRowsProps {
  cols: number;
  rows?: number;
}

export function SkeletonRows({ cols, rows = 5 }: SkeletonRowsProps) {
  return (
    <>
      {Array.from({ length: rows }, (_, i) => (
        <tr key={i}>
          {Array.from({ length: cols }, (_, j) => (
            <td key={j} className="border-t border-zinc-100 px-3 py-2.5 dark:border-zinc-800">
              <div className="h-4 rounded bg-zinc-200 motion-safe:animate-pulse dark:bg-zinc-800" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}
