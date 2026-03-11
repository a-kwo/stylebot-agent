'use client';

interface SkeletonProps {
  variant?: 'card' | 'grid' | 'text';
  count?: number;
}

function SkeletonCard() {
  return (
    <div className="card p-3 flex flex-col gap-3">
      <div className="skeleton w-full aspect-square" />
      <div className="skeleton h-4 w-3/4" />
      <div className="skeleton h-3 w-1/2" />
    </div>
  );
}

function SkeletonText() {
  return (
    <div className="flex flex-col gap-3">
      <div className="skeleton h-4 w-full" />
      <div className="skeleton h-4 w-5/6" />
      <div className="skeleton h-4 w-2/3" />
    </div>
  );
}

export default function SkeletonLoader({ variant = 'grid', count = 8 }: SkeletonProps) {
  if (variant === 'text') {
    return <SkeletonText />;
  }

  if (variant === 'card') {
    return <SkeletonCard />;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
