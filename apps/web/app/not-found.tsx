import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-8 text-center dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        Page not found
      </h2>
      <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
        The page you are looking for does not exist.
      </p>
      <Link
        href="/search"
        className="mt-4 inline-block rounded-md bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 dark:bg-orange-500 dark:hover:bg-orange-600"
      >
        Go to Search
      </Link>
    </div>
  );
}
