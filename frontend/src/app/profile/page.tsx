'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiFetch } from '@/lib/api';
import DarkModeToggle from '@/components/DarkModeToggle';
import PageHeader from '@/components/PageHeader';
import SkeletonLoader from '@/components/SkeletonLoader';
import { motion } from 'framer-motion';

export default function ProfilePage() {
  const router = useRouter();
  const { authenticated, onboarded, loading: authLoading, logout } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (authenticated === false) router.replace('/login');
    else if (onboarded === false) router.replace('/onboarding');
  }, [authenticated, onboarded, authLoading, router]);

  useEffect(() => {
    if (!authenticated || onboarded !== true) return;
    apiFetch('/profile')
      .then((r) => r.json())
      .then(setProfile)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [authenticated, onboarded]);

  if (!authenticated || onboarded !== true) return null;

  const renderPills = (arr: any) => {
    if (!arr || !Array.isArray(arr) || arr.length === 0) {
      return <span className="text-muted text-sm">None set</span>;
    }
    return (
      <div className="flex flex-wrap gap-1.5">
        {arr.map((item: string, i: number) => (
          <span
            key={i}
            className="px-2.5 py-1 text-xs font-medium rounded-full bg-accent/10 text-accent dark:bg-accent/20 dark:text-accent-light capitalize"
          >
            {item}
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <div className="flex items-center gap-4 mb-8">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="w-14 h-14 rounded-full bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center text-white font-display text-2xl font-semibold shadow-lg shadow-accent/20"
        >
          {profile?.gender?.charAt(0)?.toUpperCase() || 'S'}
        </motion.div>
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Profile</h1>
          <p className="text-muted text-sm">Your style preferences</p>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col gap-4">
          <div className="card p-4"><SkeletonLoader variant="text" /></div>
          <div className="card p-4"><SkeletonLoader variant="text" /></div>
        </div>
      ) : profile ? (
        <div className="flex flex-col gap-4">
          <div className="card p-5 border-l-2 border-accent/30">
            <h2 className="font-display text-lg font-semibold mb-4">About You</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Gender</span>
                <div className="capitalize mt-0.5">{profile.gender || 'Not set'}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Age</span>
                <div className="mt-0.5">{profile.age || 'Not set'}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Climate</span>
                <div className="capitalize mt-0.5">{profile.climate || 'Not set'}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Budget</span>
                <div className="mt-0.5">${profile.budget_min}--${profile.budget_max}</div>
              </div>
            </div>
          </div>

          <div className="card p-5 border-l-2 border-accent/30">
            <h2 className="font-display text-lg font-semibold mb-4">Style Preferences</h2>
            <div className="flex flex-col gap-3">
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Style</span>
                <div className="mt-1.5">{renderPills(profile.style_adjectives)}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Favorite Colors</span>
                <div className="mt-1.5">{renderPills(profile.preferred_colors)}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Avoided Colors</span>
                <div className="mt-1.5">{renderPills(profile.avoided_colors)}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Favorite Brands</span>
                <div className="mt-1.5">{renderPills(profile.preferred_brands)}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Fit</span>
                <div className="mt-1.5">{renderPills(profile.fit_preferences)}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Occasions</span>
                <div className="mt-1.5">{renderPills(profile.occasions)}</div>
              </div>
            </div>
          </div>

          <div className="card p-5 border-l-2 border-accent/30">
            <h2 className="font-display text-lg font-semibold mb-4">Sizes</h2>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Tops</span>
                <div className="mt-0.5">{profile.size_tops || '---'}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Bottoms</span>
                <div className="mt-0.5">{profile.size_bottoms || '---'}</div>
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted font-medium">Shoes</span>
                <div className="mt-0.5">{profile.size_shoes || '---'}</div>
              </div>
            </div>
          </div>

          <div className="card p-5 flex items-center justify-between">
            <span className="text-sm font-medium">Appearance</span>
            <DarkModeToggle />
          </div>

          <button
            onClick={() => {
              logout();
            }}
            className="px-6 py-3 rounded-xl font-medium text-red-600 border-2 border-red-200 dark:border-red-900/30 hover:bg-red-50 dark:hover:bg-red-900/10 transition-all"
          >
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}
