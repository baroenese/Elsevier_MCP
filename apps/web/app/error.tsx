'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-500/30 dark:bg-red-500/10">
      <h2 className="text-lg font-semibold text-red-800 dark:text-red-400">
        Something went wrong
      </h2>
      <p className="mt-2 text-sm text-red-700 dark:text-red-300">
        {error.message || 'An unexpected error occurred while rendering this page.'}
      </p>
      {error.digest ? (
        <p className="mt-1 font-mono text-xs text-red-600 dark:text-red-400/80">
          digest: {error.digest}
        </p>
      ) : null}
      <button
        onClick={reset}
        className="mt-4 rounded-md bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 dark:bg-orange-500 dark:hover:bg-orange-600"
      >
        Try again
      </button>
    </div>
  );
}
