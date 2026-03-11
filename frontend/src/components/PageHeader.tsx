'use client';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actionLabel?: string;
  onAction?: () => void;
  children?: React.ReactNode;
}

export default function PageHeader({ title, subtitle, actionLabel, onAction, children }: PageHeaderProps) {
  return (
    <div className="mb-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">{title}</h1>
          {subtitle && (
            <p className="text-muted text-sm mt-1">{subtitle}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {children}
          {actionLabel && onAction && (
            <button onClick={onAction} className="btn-secondary text-sm px-4 py-2">
              {actionLabel}
            </button>
          )}
        </div>
      </div>
      <div className="rule mt-5" />
    </div>
  );
}
