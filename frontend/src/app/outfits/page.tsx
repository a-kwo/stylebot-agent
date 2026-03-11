'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiFetch } from '@/lib/api';
import { Trash2, Layers } from 'lucide-react';
import { motion } from 'framer-motion';
import PageHeader from '@/components/PageHeader';
import SkeletonLoader from '@/components/SkeletonLoader';
import EmptyState from '@/components/EmptyState';

interface OutfitItem {
  id: number;
  name: string;
  category: string;
  color?: string;
  image_url?: string;
}

interface Outfit {
  id: number;
  name: string;
  occasion?: string;
  season?: string;
  notes?: string;
  items: OutfitItem[];
  created_at: string;
}

export default function OutfitsPage() {
  const router = useRouter();
  const { authenticated, onboarded, loading: authLoading } = useAuth();
  const [outfits, setOutfits] = useState<Outfit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (authenticated === false) router.replace('/login');
    else if (onboarded === false) router.replace('/onboarding');
  }, [authenticated, onboarded, authLoading, router]);

  useEffect(() => {
    if (!authenticated || onboarded !== true) return;
    loadOutfits();
  }, [authenticated, onboarded]);

  const loadOutfits = async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/outfits');
      setOutfits(await res.json());
    } catch {}
    setLoading(false);
  };

  const deleteOutfit = async (id: number) => {
    await apiFetch(`/outfits/${id}`, { method: 'DELETE' });
    setOutfits((prev) => prev.filter((o) => o.id !== id));
  };

  if (!authenticated || onboarded !== true) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <PageHeader
        title="My Outfits"
        subtitle={`${outfits.length} saved outfit${outfits.length !== 1 ? 's' : ''}`}
      />

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-4">
              <div className="skeleton h-5 w-1/2 mb-3" />
              <div className="skeleton h-3 w-1/3 mb-4" />
              <div className="flex gap-2">
                {Array.from({ length: 3 }).map((_, j) => (
                  <div key={j} className="skeleton w-16 h-16 rounded-lg" />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : outfits.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="No outfits saved yet"
          description="Build an outfit in the Outfit Builder or ask StyleBot to put one together"
          actionLabel="Build an Outfit"
          onAction={() => router.push('/builder')}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {outfits.map((outfit, i) => (
            <motion.div
              key={outfit.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.3 }}
              className="card-hover p-4 group"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-display text-lg font-semibold">{outfit.name}</h3>
                  <div className="flex gap-2 mt-1.5">
                    {outfit.occasion && (
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-accent/10 text-accent dark:bg-accent/20 dark:text-accent-light capitalize font-medium">
                        {outfit.occasion}
                      </span>
                    )}
                    {outfit.season && (
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-gold/10 text-gold dark:bg-gold/20 capitalize font-medium">
                        {outfit.season}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => deleteOutfit(outfit.id)}
                  className="p-1.5 rounded-lg text-red-500 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {outfit.notes && (
                <p className="text-sm text-muted mb-3">{outfit.notes}</p>
              )}

              <div className="flex gap-2 overflow-x-auto pb-1">
                {outfit.items.map((item) => (
                  <div
                    key={item.id}
                    className="shrink-0 w-16 text-center"
                  >
                    {item.image_url ? (
                      <img
                        src={item.image_url}
                        alt={item.name}
                        className="w-16 h-16 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-16 h-16 rounded-lg bg-cream-dark dark:bg-surface-dark-2 flex items-center justify-center text-xs text-muted capitalize">
                        {item.category}
                      </div>
                    )}
                    <div className="text-[10px] mt-1 truncate">{item.name}</div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
