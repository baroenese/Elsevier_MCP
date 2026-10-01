export default function Loading() {
  return (
    <div className="animate-pulse space-y-4" aria-busy="true" aria-label="Loading">
      <div className="h-10 w-full max-w-xl rounded-md bg-zinc-200 dark:bg-zinc-800" />
      <div className="h-32 w-full rounded-lg bg-zinc-200 dark:bg-zinc-800" />
      <div className="h-64 w-full rounded-lg bg-zinc-200 dark:bg-zinc-800" />
    </div>
  );
}
