'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { login, register } from '@/lib/api';
import { motion } from 'framer-motion';

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
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background gradient layers */}
      <div className="absolute inset-0 bg-gradient-to-br from-cream via-white to-accent-50 dark:from-surface-dark dark:via-surface-dark-1 dark:to-surface-dark" />
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-accent/[0.03] dark:bg-accent/[0.06] rounded-full blur-3xl -translate-y-1/3 translate-x-1/3" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gold/[0.03] dark:bg-gold/[0.04] rounded-full blur-3xl translate-y-1/3 -translate-x-1/3" />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-sm relative z-10"
      >
        {/* Brand */}
        <div className="text-center mb-10">
          <motion.h1
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="font-display text-5xl font-semibold tracking-tight mb-3"
          >
            StyleBot
          </motion.h1>
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.5, duration: 0.6, ease: 'easeOut' }}
            className="w-16 h-[1.5px] bg-accent mx-auto mb-3"
          />
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="font-display text-lg italic text-muted"
          >
            Your personal styling&nbsp;assistant
          </motion.p>
        </div>

        {/* Card */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="card backdrop-blur-md bg-white/80 dark:bg-surface-dark-1/80 p-7 shadow-lg shadow-ink/[0.04] dark:shadow-black/20"
        >
          {/* Tabs */}
          <div className="relative flex mb-7">
            <button
              onClick={() => { setTab('login'); setError(''); }}
              className={`relative z-10 flex-1 pb-3 text-sm font-medium transition-colors ${
                tab === 'login' ? 'text-ink dark:text-white' : 'text-muted'
              }`}
            >
              Sign in
            </button>
            <button
              onClick={() => { setTab('register'); setError(''); }}
              className={`relative z-10 flex-1 pb-3 text-sm font-medium transition-colors ${
                tab === 'register' ? 'text-ink dark:text-white' : 'text-muted'
              }`}
            >
              Create account
            </button>
            {/* Bottom border */}
            <div className="absolute bottom-0 left-0 right-0 h-px bg-border dark:bg-surface-dark-3" />
            {/* Active indicator */}
            <motion.div
              layoutId="auth-tab"
              className="absolute bottom-0 h-[2px] w-1/2 bg-accent dark:bg-accent-light"
              style={{ left: tab === 'login' ? '0%' : '50%' }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="block text-[11px] font-medium uppercase tracking-[0.1em] text-muted mb-1.5">Username</label>
              <input
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field"
                required
                minLength={3}
                autoComplete="username"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium uppercase tracking-[0.1em] text-muted mb-1.5">Password</label>
              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                required
                minLength={6}
                autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
              />
            </div>

            {error && (
              <p className="text-red-500 text-sm">{error}</p>
            )}

            <button type="submit" disabled={loading} className="btn-primary mt-1">
              {loading
                ? (tab === 'login' ? 'Signing in...' : 'Creating account...')
                : (tab === 'login' ? 'Sign in' : 'Create account')
              }
            </button>
          </form>
        </motion.div>

        {/* Footer note */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="text-center text-xs text-muted/60 mt-6"
        >
          AI-powered style recommendations
        </motion.p>
      </motion.div>
    </div>
  );
}
