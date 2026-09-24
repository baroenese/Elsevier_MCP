interface StatusTextProps {
  message: string;
  isError?: boolean;
}

export function StatusText({ message, isError }: StatusTextProps) {
  return (
    <span className={`text-[13px] ${isError ? 'text-red-600 dark:text-red-400' : 'text-zinc-500 dark:text-zinc-400'}`}>
      {message}
    </span>
  );
}
