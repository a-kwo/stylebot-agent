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
  tags: string[];
  image_url?: string;
}

type SlotKey = 'tops' | 'bottoms' | 'shoes' | 'outerwear' | 'accessories';

const SLOT_LABELS: Record<SlotKey, string> = {
  tops: 'Top',
  bottoms: 'Bottom',
  shoes: 'Shoes',
  outerwear: 'Outerwear',
  accessories: 'Accessory',
};

const CATEGORIES: SlotKey[] = ['tops', 'bottoms', 'shoes', 'outerwear', 'accessories'];

const OCCASIONS = ['casual', 'work', 'date', 'formal', 'gym', 'travel'];
const SEASONS = ['spring', 'summer', 'fall', 'winter', 'all-season'];

export default function BuilderPage() {
  const router = useRouter();
  const { authenticated, onboarded, loading: authLoading } = useAuth();

  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [filter, setFilter] = useState<SlotKey | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [slots, setSlots] = useState<Record<SlotKey, WardrobeItem | null>>({
    tops: null,
    bottoms: null,
    shoes: null,
    outerwear: null,
    accessories: null,
  });

  // Save form state
  const [outfitName, setOutfitName] = useState('');
  const [occasion, setOccasion] = useState('');
  const [season, setSeason] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');

  // Feedback state
  const [feedback, setFeedback] = useState('');
  const [askingFeedback, setAskingFeedback] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (authenticated === false) router.replace('/');
    else if (onboarded === false) router.replace('/onboarding');
  }, [authenticated, onboarded, authLoading, router]);

  useEffect(() => {
    if (!authenticated || onboarded !== true) return;
    loadWardrobe();
  }, [authenticated, onboarded]);

  const loadWardrobe = async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/wardrobe');
      setItems(await res.json());
    } catch {}
    setLoading(false);
  };

  const filteredItems = filter === 'all'
    ? items
    : items.filter((i) => i.category === filter);

  const addToSlot = (item: WardrobeItem) => {
    const slotKey = item.category as SlotKey;
    if (CATEGORIES.includes(slotKey)) {
      setSlots((prev) => ({ ...prev, [slotKey]: item }));
    }
  };

  const removeFromSlot = (slotKey: SlotKey) => {
    setSlots((prev) => ({ ...prev, [slotKey]: null }));
  };

  const filledSlots = Object.values(slots).filter(Boolean) as WardrobeItem[];

  const saveOutfit = async () => {
    if (!outfitName.trim() || filledSlots.length === 0) return;
    setSaving(true);
    setSaveMsg('');
    try {
      const res = await apiFetch('/outfits', {
        method: 'POST',
        body: JSON.stringify({
          name: outfitName.trim(),
          occasion: occasion || undefined,
          season: season || undefined,
          wardrobe_item_ids: filledSlots.map((i) => i.id),
        }),
      });
      if (res.ok) {
        setSaveMsg('Outfit saved!');
        setOutfitName('');
        setOccasion('');
        setSeason('');
      } else {
        setSaveMsg('Failed to save.');
      }
    } catch {
      setSaveMsg('Failed to save.');
    }
    setSaving(false);
  };

  const askStyleBot = async () => {
    if (filledSlots.length === 0) return;
    setAskingFeedback(true);
    setFeedback('');
    try {
      const message = `Give me feedback on this outfit: ${filledSlots.map((i) => i.name).join(', ')}${occasion ? ` for ${occasion}` : ''}`;
      const res = await apiFetch('/chat', {
        method: 'POST',
        body: JSON.stringify({ message }),
      });
      if (res.ok) {
        const data = await res.json();
        setFeedback(data.reply || data.text || JSON.stringify(data));
      }
    } catch {
      setFeedback('Could not get feedback right now.');
    }
    setAskingFeedback(false);
  };

  if (!authenticated || onboarded !== true) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Outfit Builder</h1>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left panel: Wardrobe grid */}
        <div className="lg:w-1/2">
          <h2 className="text-lg font-semibold mb-3">Your Wardrobe</h2>

          {/* Category filter */}
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                filter === 'all'
                  ? 'bg-ink text-cream dark:bg-cream dark:text-ink'
                  : 'bg-zinc-100 dark:bg-zinc-800 text-muted hover:text-ink dark:hover:text-cream'
              }`}
            >
              All
            </button>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
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
            <div className="text-center text-muted py-8">Loading...</div>
          ) : filteredItems.length === 0 ? (
            <div className="text-center text-muted py-8">
              <p>No items found</p>
            </div>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
              {filteredItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => addToSlot(item)}
                  className="card p-2 text-left hover:ring-2 hover:ring-ink dark:hover:ring-cream transition-all"
                >
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={item.name}
                      className="w-full aspect-square object-cover rounded-lg"
                    />
                  ) : (
                    <div className="w-full aspect-square bg-zinc-100 dark:bg-zinc-700 rounded-lg flex items-center justify-center text-xl text-muted">
                      {item.category.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div className="text-xs font-medium mt-1 truncate">{item.name}</div>
                  <div className="text-[10px] text-muted capitalize">{item.category}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right panel: Outfit canvas */}
        <div className="lg:w-1/2">
          <h2 className="text-lg font-semibold mb-3">Outfit Canvas</h2>

          {/* Slots */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
            {CATEGORIES.map((slotKey) => {
              const item = slots[slotKey];
              return (
                <div
                  key={slotKey}
                  className="card p-3 flex flex-col items-center text-center min-h-[120px]"
                >
                  <div className="text-xs text-muted mb-2 font-medium">
                    {SLOT_LABELS[slotKey]}
                  </div>
                  {item ? (
                    <>
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-16 h-16 object-cover rounded-lg"
                        />
                      ) : (
                        <div className="w-16 h-16 bg-zinc-100 dark:bg-zinc-700 rounded-lg flex items-center justify-center text-lg text-muted">
                          {item.category.charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div className="text-xs font-medium mt-1 truncate w-full">
                        {item.name}
                      </div>
                      <button
                        onClick={() => removeFromSlot(slotKey)}
                        className="text-[10px] text-red-500 hover:text-red-700 mt-1"
                      >
                        Remove
                      </button>
                    </>
                  ) : (
                    <div className="flex-1 flex items-center justify-center text-muted text-sm">
                      Empty
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Save form */}
          {filledSlots.length > 0 && (
            <div className="card p-4 mb-4">
              <h3 className="text-sm font-semibold mb-3">Save Outfit</h3>
              <input
                type="text"
                placeholder="Outfit name"
                value={outfitName}
                onChange={(e) => setOutfitName(e.target.value)}
                className="input-field w-full mb-2"
              />
              <div className="flex gap-2 mb-2">
                <select
                  value={occasion}
                  onChange={(e) => setOccasion(e.target.value)}
                  className="input-field flex-1"
                >
                  <option value="">Occasion</option>
                  {OCCASIONS.map((o) => (
                    <option key={o} value={o}>
                      {o.charAt(0).toUpperCase() + o.slice(1)}
                    </option>
                  ))}
                </select>
                <select
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  className="input-field flex-1"
                >
                  <option value="">Season</option>
                  {SEASONS.map((s) => (
                    <option key={s} value={s}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={saveOutfit}
                disabled={!outfitName.trim() || saving}
                className="btn-primary w-full"
              >
                {saving ? 'Saving...' : 'Save Outfit'}
              </button>
              {saveMsg && (
                <div className="text-sm text-center mt-2 text-muted">{saveMsg}</div>
              )}
            </div>
          )}

          {/* Ask StyleBot */}
          {filledSlots.length > 0 && (
            <button
              onClick={askStyleBot}
              disabled={askingFeedback}
              className="btn-primary w-full mb-4"
            >
              {askingFeedback ? 'Asking StyleBot...' : 'Ask StyleBot for Feedback'}
            </button>
          )}

          {feedback && (
            <div className="card p-4">
              <h3 className="text-sm font-semibold mb-2">StyleBot Feedback</h3>
              <p className="text-sm text-muted whitespace-pre-wrap">{feedback}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
