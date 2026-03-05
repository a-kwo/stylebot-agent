'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiFetch } from '@/lib/api';

interface WardrobeItem {
  id: number;
  name: string;
  category: string;
  color?: string;
  brand?: string;
  condition: string;
  tags: string[];
  image_url?: string;
  local_image_path?: string;
}

const CATEGORIES = ['all', 'tops', 'bottoms', 'shoes', 'outerwear', 'accessories', 'dresses'];

function proxyUrl(url: string): string {
  return `/api/images/proxy?url=${encodeURIComponent(url)}`;
}

export default function WardrobePage() {
  const router = useRouter();
  const { authenticated, onboarded, loading: authLoading } = useAuth();
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [imgErrors, setImgErrors] = useState<Record<number, number>>({});

  useEffect(() => {
    if (authLoading) return;
    if (authenticated === false) router.replace('/');
    else if (onboarded === false) router.replace('/onboarding');
  }, [authenticated, onboarded, authLoading, router]);

  useEffect(() => {
    if (!authenticated || onboarded !== true) return;
    loadItems();
  }, [authenticated, onboarded, filter]);

  const loadItems = async () => {
    setLoading(true);
    try {
      const path = filter === 'all' ? '/wardrobe' : `/wardrobe?category=${filter}`;
      const res = await apiFetch(path);
      setItems(await res.json());
    } catch {}
    setLoading(false);
  };

  const deleteItem = async (id: number) => {
    await apiFetch(`/wardrobe/${id}`, { method: 'DELETE' });
    setItems((prev) => prev.filter((i) => i.id !== id));
  };

  if (!authenticated || onboarded !== true) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">My Wardrobe</h1>

      {/* Category filter */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              filter === cat
                ? 'bg-ink text-cream dark:bg-cream dark:text-ink'
                : 'bg-zinc-100 dark:bg-zinc-800 text-muted hover:text-ink dark:hover:text-cream'
            }`}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center text-muted py-12">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-muted py-12">
          <p className="text-lg mb-2">No items yet</p>
          <p className="text-sm">
            Tell StyleBot about clothes you own and they&apos;ll appear here
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {items.map((item) => (
            <div key={item.id} className="card p-3 flex flex-col gap-2">
              {(() => {
                const errors = imgErrors[item.id] || 0;
                const hasUrl = item.local_image_path || item.image_url;
                // Stage 0: local_image_path or proxy URL
                // Stage 1: direct URL (proxy failed, try browser-direct)
                // Stage 2+: placeholder
                if (hasUrl && errors === 0) {
                  return (
                    <img
                      src={item.local_image_path || proxyUrl(item.image_url!)}
                      alt={item.name}
                      className="w-full aspect-square object-cover rounded-xl"
                      onError={() => setImgErrors((prev) => ({ ...prev, [item.id]: 1 }))}
                    />
                  );
                }
                if (item.image_url && errors === 1) {
                  return (
                    <img
                      src={item.image_url}
                      alt={item.name}
                      className="w-full aspect-square object-cover rounded-xl"
                      onError={() => setImgErrors((prev) => ({ ...prev, [item.id]: 2 }))}
                    />
                  );
                }
                return (
                  <div className="w-full aspect-square bg-zinc-100 dark:bg-zinc-700 rounded-xl flex items-center justify-center text-2xl text-muted">
                    {item.category.charAt(0).toUpperCase()}
                  </div>
                );
              })()}
              <div className="text-sm font-medium">{item.name}</div>
              <div className="flex items-center gap-2 text-xs text-muted">
                <span className="capitalize">{item.category}</span>
                {item.color && <span>{item.color}</span>}
              </div>
              {item.brand && (
                <div className="text-xs text-muted">{item.brand}</div>
              )}
              <button
                onClick={() => deleteItem(item.id)}
                className="text-xs text-red-500 hover:text-red-700 mt-auto self-start"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
