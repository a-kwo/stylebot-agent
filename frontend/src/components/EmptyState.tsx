'use client';

import { type LucideIcon } from 'lucide-react';
import { motion } from 'framer-motion';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({ icon: Icon, title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center justify-center py-20 px-4"
    >
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-accent/8 dark:bg-accent/10 flex items-center justify-center">
          <Icon className="w-7 h-7 text-accent/70 dark:text-accent-light/70" strokeWidth={1.5} />
        </div>
        <div className="absolute -inset-3 rounded-3xl border border-dashed border-accent/15 dark:border-accent-light/15" />
      </div>
      <h3 className="font-display text-xl font-semibold mb-1.5">{title}</h3>
      {description && (
        <p className="text-muted text-sm text-center max-w-xs leading-relaxed">{description}</p>
      )}
      {actionLabel && onAction && (
        <button onClick={onAction} className="btn-secondary mt-5 text-sm px-5 py-2.5">
          {actionLabel}
        </button>
      )}
    </motion.div>
  );
}
