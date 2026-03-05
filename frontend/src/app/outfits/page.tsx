'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiFetch } from '@/lib/api';

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
    if (authenticated === false) router.replace('/');
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
      <h1 className="text-2xl font-bold mb-6">My Outfits</h1>

      {loading ? (
        <div className="text-center text-muted py-12">Loading...</div>
      ) : outfits.length === 0 ? (
        <div className="text-center text-muted py-12">
          <p className="text-lg mb-2">No outfits saved yet</p>
          <p className="text-sm">
            Ask StyleBot to put together an outfit and save it here
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {outfits.map((outfit) => (
            <div key={outfit.id} className="card p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold">{outfit.name}</h3>
                  <div className="flex gap-2 text-xs text-muted mt-1">
                    {outfit.occasion && (
                      <span className="bg-zinc-100 dark:bg-zinc-700 px-2 py-0.5 rounded-full capitalize">
                        {outfit.occasion}
                      </span>
                    )}
                    {outfit.season && (
                      <span className="bg-zinc-100 dark:bg-zinc-700 px-2 py-0.5 rounded-full capitalize">
                        {outfit.season}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => deleteOutfit(outfit.id)}
                  className="text-xs text-red-500 hover:text-red-700"
                >
                  Delete
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
                      <div className="w-16 h-16 rounded-lg bg-zinc-100 dark:bg-zinc-700 flex items-center justify-center text-xs text-muted capitalize">
                        {item.category}
                      </div>
                    )}
                    <div className="text-[10px] mt-1 truncate">{item.name}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
