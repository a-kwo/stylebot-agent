'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import DarkModeToggle from '@/components/DarkModeToggle';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const navLinks = [
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How It Works' },
  { href: '#about', label: 'About' },
];

export default function LandingNav() {
  const { authenticated } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 32);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'backdrop-blur-xl bg-white/70 dark:bg-surface-dark/80 border-b border-border/60 dark:border-surface-dark-3/60'
          : 'bg-transparent'
      }`}
    >
      <nav className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="font-display text-2xl font-semibold tracking-tight text-accent dark:text-accent-light">
          StyleBot
        </a>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-[13px] font-medium text-muted hover:text-ink dark:hover:text-zinc-200 transition-colors tracking-wide uppercase"
            >
              {link.label}
            </a>
          ))}
          <div className="w-px h-5 bg-border dark:bg-surface-dark-3" />
          <DarkModeToggle />
          <a
            href={authenticated ? '/chat' : '/login'}
            className="btn-primary text-sm px-5 py-2.5"
          >
            {authenticated ? 'Go to App' : 'Try StyleBot'}
          </a>
        </div>

        {/* Mobile controls */}
        <div className="flex md:hidden items-center gap-2">
          <DarkModeToggle />
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="btn-ghost p-2"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="md:hidden overflow-hidden backdrop-blur-xl bg-white/90 dark:bg-surface-dark/95 border-b border-border/60 dark:border-surface-dark-3/60"
          >
            <div className="px-6 py-4 flex flex-col gap-3">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="text-sm font-medium text-muted hover:text-ink dark:hover:text-zinc-200 transition-colors py-1"
                >
                  {link.label}
                </a>
              ))}
              <div className="rule my-1" />
              <a
                href={authenticated ? '/chat' : '/login'}
                className="btn-primary text-sm text-center"
                onClick={() => setMobileOpen(false)}
              >
                {authenticated ? 'Go to App' : 'Try StyleBot'}
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
