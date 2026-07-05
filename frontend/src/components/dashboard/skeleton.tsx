export function SkeletonBlock({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={`animate-pulse rounded-lg bg-[var(--journal-accent-soft)] ${className}`}
    />
  );
}

export function CardsSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonBlock key={i} className="h-24" />
      ))}
    </div>
  );
}

export function RowsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonBlock key={i} className="h-16" />
      ))}
    </div>
  );
}
