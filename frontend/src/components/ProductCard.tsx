'use client';

import { submitFeedback } from '@/lib/api';
import { useState } from 'react';

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

export default function ProductCard({ item }: { item: Product }) {
  const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);
  const [imgErrors, setImgErrors] = useState(0);

  const handleFeedback = (type: 'like' | 'dislike') => {
    setFeedback(type);
    submitFeedback(item.title, type).catch(() => {});
  };

  return (
    <div className="card overflow-hidden flex flex-col">
      {item.image_url && imgErrors === 0 ? (
        <img
          src={proxyUrl(item.image_url)}
          alt={item.title}
          className="w-full aspect-square object-cover"
          loading="lazy"
          onError={() => setImgErrors(1)}
        />
      ) : item.image_url && imgErrors === 1 ? (
        <img
          src={item.image_url}
          alt={item.title}
          className="w-full aspect-square object-cover"
          loading="lazy"
          onError={() => setImgErrors(2)}
        />
      ) : (
        <div className="w-full aspect-square bg-zinc-100 dark:bg-zinc-700 flex items-center justify-center text-3xl">
          ?
        </div>
      )}

      <div className="p-3 flex flex-col gap-1.5 flex-1">
        <div className="text-sm font-medium line-clamp-2">{item.title}</div>
        <div className="flex items-center gap-2 text-sm">
          {item.price && (
            <span className="font-semibold">
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
              className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
            >
              View Product
            </a>
          )}
          <div className="flex gap-1 ml-auto">
            <button
              onClick={() => handleFeedback('like')}
              className={`text-lg transition-transform hover:scale-110 ${
                feedback === 'like' ? 'scale-110' : 'opacity-50'
              }`}
            >
              +
            </button>
            <button
              onClick={() => handleFeedback('dislike')}
              className={`text-lg transition-transform hover:scale-110 ${
                feedback === 'dislike' ? 'scale-110' : 'opacity-50'
              }`}
            >
              -
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
