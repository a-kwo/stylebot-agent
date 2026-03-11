'use client';

import { submitFeedback } from '@/lib/api';
import { useState } from 'react';
import { ThumbsUp, ThumbsDown, ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';

interface Product {
  title: string;
  price?: number;
  image_url?: string;
  item_url?: string;
  seller?: string;
}

function proxyUrl(url: string): string {
  return `/api/images/proxy?url=${encodeURIComponent(url)}`;
}

export default function ProductCard({ item, index = 0 }: { item: Product; index?: number }) {
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);
  const [imgErrors, setImgErrors] = useState(0);

  const handleFeedback = (type: 'like' | 'dislike') => {
    setFeedback(type);
    submitFeedback(item.title, type).catch(() => {});
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="card-hover overflow-hidden flex flex-col group"
    >
      {item.image_url && imgErrors === 0 ? (
        <div className="overflow-hidden">
          <img
            src={proxyUrl(item.image_url)}
            alt={item.title}
            className="w-full aspect-square object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
            onError={() => setImgErrors(1)}
          />
        </div>
      ) : item.image_url && imgErrors === 1 ? (
        <div className="overflow-hidden">
          <img
            src={item.image_url}
            alt={item.title}
            className="w-full aspect-square object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
            onError={() => setImgErrors(2)}
          />
        </div>
      ) : (
        <div className="w-full aspect-square bg-cream-dark dark:bg-surface-dark-2 flex items-center justify-center text-3xl text-muted">
          ?
        </div>
      )}

      <div className="p-3 flex flex-col gap-1.5 flex-1">
        <div className="text-sm font-medium line-clamp-2">{item.title}</div>
        <div className="flex items-center gap-2 text-sm">
          {item.price && (
            <span className="font-display text-lg font-semibold text-accent dark:text-accent-light">
              ${parseFloat(String(item.price)).toFixed(2)}
            </span>
          )}
          {item.seller && (
            <span className="text-muted text-xs">{item.seller}</span>
          )}
        </div>

        <div className="flex items-center gap-2 mt-auto pt-2">
          {item.item_url && (
            <a
              href={item.item_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs font-medium text-accent dark:text-accent-light hover:underline"
            >
              <ExternalLink className="w-3 h-3" />
              View
            </a>
          )}
          <div className="flex gap-1.5 ml-auto">
            <button
              onClick={() => handleFeedback('like')}
              className={`p-1.5 rounded-lg transition-all ${
                feedback === 'like'
                  ? 'text-accent bg-accent/10'
                  : 'text-muted hover:text-accent hover:bg-accent/5'
              }`}
            >
              <ThumbsUp className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => handleFeedback('dislike')}
              className={`p-1.5 rounded-lg transition-all ${
                feedback === 'dislike'
                  ? 'text-red-500 bg-red-500/10'
                  : 'text-muted hover:text-red-500 hover:bg-red-500/5'
              }`}
            >
              <ThumbsDown className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
