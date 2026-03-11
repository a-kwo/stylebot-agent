'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiFetch } from '@/lib/api';
import { Trash2, Shirt } from 'lucide-react';
import { motion } from 'framer-motion';
import PageHeader from '@/components/PageHeader';
import SkeletonLoader from '@/components/SkeletonLoader';
import EmptyState from '@/components/EmptyState';

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
    if (authenticated === false) router.replace('/login');
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

  const categoryCount = (cat: string) => {
    if (cat === 'all') return items.length;
    return items.filter((i) => i.category === cat).length;
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <PageHeader title="My Wardrobe" subtitle={`${items.length} pieces in your collection`} />

      {/* Category filter */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all duration-200 ${
              filter === cat
                ? 'bg-accent text-white shadow-md shadow-accent/20'
                : 'bg-cream-dark dark:bg-surface-dark-2 text-muted hover:text-ink dark:hover:text-cream'
            }`}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
            {!loading && (
              <span className={`text-xs ${filter === cat ? 'text-white/70' : 'text-muted'}`}>
                {categoryCount(cat)}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <SkeletonLoader variant="grid" count={8} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Shirt}
          title="No items yet"
          description="Tell StyleBot about clothes you own and they'll appear here"
          actionLabel="Chat with StyleBot"
          onAction={() => router.push('/chat')}
        />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {items.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04, duration: 0.3 }}
              className="card-hover p-3 flex flex-col gap-2 group"
            >
              {(() => {
                const errors = imgErrors[item.id] || 0;
                const hasUrl = item.local_image_path || item.image_url;
                if (hasUrl && errors === 0) {
                  return (
                    <div className="overflow-hidden rounded-xl">
                      <img
                        src={item.local_image_path || proxyUrl(item.image_url!)}
                        alt={item.name}
                        className="w-full aspect-square object-cover transition-transform duration-500 group-hover:scale-105"
                        onError={() => setImgErrors((prev) => ({ ...prev, [item.id]: 1 }))}
                      />
                    </div>
                  );
                }
                if (item.image_url && errors === 1) {
                  return (
                    <div className="overflow-hidden rounded-xl">
                      <img
                        src={item.image_url}
                        alt={item.name}
                        className="w-full aspect-square object-cover transition-transform duration-500 group-hover:scale-105"
                        onError={() => setImgErrors((prev) => ({ ...prev, [item.id]: 2 }))}
                      />
                    </div>
                  );
                }
                return (
                  <div className="w-full aspect-square bg-cream-dark dark:bg-surface-dark-2 rounded-xl flex items-center justify-center text-2xl text-muted">
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
                className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700 mt-auto self-start opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 className="w-3 h-3" />
                Remove
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
