'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiFetch } from '@/lib/api';
import DarkModeToggle from '@/components/DarkModeToggle';

export default function ProfilePage() {
  const router = useRouter();
  const { authenticated, onboarded, loading: authLoading, logout } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (authenticated === false) router.replace('/');
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

  const fmtList = (arr: any) => {
    if (!arr || !Array.isArray(arr) || arr.length === 0) return 'None set';
    return arr.join(', ');
  };

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Profile</h1>

      {loading ? (
        <div className="text-center text-muted py-12">Loading...</div>
      ) : profile ? (
        <div className="flex flex-col gap-4">
          <div className="card p-4">
            <h2 className="font-semibold mb-3">About You</h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-muted">Gender:</span>{' '}
                <span className="capitalize">{profile.gender || 'Not set'}</span>
              </div>
              <div>
                <span className="text-muted">Age:</span>{' '}
                {profile.age || 'Not set'}
              </div>
              <div>
                <span className="text-muted">Climate:</span>{' '}
                <span className="capitalize">{profile.climate || 'Not set'}</span>
              </div>
              <div>
                <span className="text-muted">Budget:</span>{' '}
                ${profile.budget_min}–${profile.budget_max}
              </div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="font-semibold mb-3">Style Preferences</h2>
            <div className="flex flex-col gap-2 text-sm">
              <div>
                <span className="text-muted">Style:</span>{' '}
                {fmtList(profile.style_adjectives)}
              </div>
              <div>
                <span className="text-muted">Favorite colors:</span>{' '}
                {fmtList(profile.preferred_colors)}
              </div>
              <div>
                <span className="text-muted">Avoided colors:</span>{' '}
                {fmtList(profile.avoided_colors)}
              </div>
              <div>
                <span className="text-muted">Favorite brands:</span>{' '}
                {fmtList(profile.preferred_brands)}
              </div>
              <div>
                <span className="text-muted">Fit:</span>{' '}
                {fmtList(profile.fit_preferences)}
              </div>
              <div>
                <span className="text-muted">Occasions:</span>{' '}
                {fmtList(profile.occasions)}
              </div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="font-semibold mb-3">Sizes</h2>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div>
                <span className="text-muted">Tops:</span>{' '}
                {profile.size_tops || '—'}
              </div>
              <div>
                <span className="text-muted">Bottoms:</span>{' '}
                {profile.size_bottoms || '—'}
              </div>
              <div>
                <span className="text-muted">Shoes:</span>{' '}
                {profile.size_shoes || '—'}
              </div>
            </div>
          </div>

          <div className="card p-4 flex items-center justify-between">
            <span className="text-sm font-medium">Appearance</span>
            <DarkModeToggle />
          </div>

          <button
            onClick={() => {
              logout();
              router.replace('/');
            }}
            className="btn-primary bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700 dark:text-white"
          >
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}
