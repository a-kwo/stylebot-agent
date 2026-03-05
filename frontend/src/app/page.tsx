'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { login, register } from '@/lib/api';

export default function AuthPage() {
  const router = useRouter();
  const { authenticated, onboarded, refresh } = useAuth();
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (authenticated && onboarded !== null) {
      router.replace(onboarded ? '/chat' : '/onboarding');
    }
  }, [authenticated, onboarded, router]);

  if (authenticated) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (tab === 'login') {
        await login(username, password);
      } else {
        await register(username, password);
      }
      refresh();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-bold text-center mb-2 tracking-tight">
          StyleBot
        </h1>
        <p className="text-center text-muted mb-8">
          Your AI styling assistant
        </p>

        <div className="card p-6">
          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-zinc-100 dark:bg-zinc-700 rounded-xl p-1">
            <button
              onClick={() => { setTab('login'); setError(''); }}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${
                tab === 'login'
                  ? 'bg-white dark:bg-zinc-800 shadow-sm'
                  : 'text-muted'
              }`}
            >
              Sign in
            </button>
            <button
              onClick={() => { setTab('register'); setError(''); }}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${
                tab === 'register'
                  ? 'bg-white dark:bg-zinc-800 shadow-sm'
                  : 'text-muted'
              }`}
            >
              Create account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              required
              minLength={3}
              autoComplete="username"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              required
              minLength={6}
              autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
            />

            {error && (
              <p className="text-red-500 text-sm">{error}</p>
            )}

            <button type="submit" disabled={loading} className="btn-primary">
              {loading
                ? (tab === 'login' ? 'Signing in...' : 'Creating account...')
                : (tab === 'login' ? 'Sign in' : 'Create account')
              }
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
