'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { MessageSquare, Shirt, Palette, Layers, User, LogOut } from 'lucide-react';
import DarkModeToggle from './DarkModeToggle';

const navItems = [
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/wardrobe', label: 'Wardrobe', icon: Shirt },
  { href: '/builder', label: 'Builder', icon: Palette },
  { href: '/outfits', label: 'Outfits', icon: Layers },
  { href: '/profile', label: 'Profile', icon: User },
];

export default function NavBar() {
  const pathname = usePathname();
  const { authenticated, logout } = useAuth();

  if (!authenticated || pathname === '/' || pathname === '/login') return null;

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-56 h-screen fixed left-0 top-0 backdrop-blur-xl bg-white/70 dark:bg-surface-dark/80 border-r border-border/60 dark:border-surface-dark-3/60 z-40">
        <div className="px-5 pt-6 pb-2">
          <div className="font-display text-2xl font-semibold tracking-tight text-accent dark:text-accent-light">
            StyleBot
          </div>
          <div className="font-display text-[11px] italic text-muted mt-0.5 tracking-wide">Personal Stylist</div>
          <div className="rule mt-4" />
        </div>

        <nav className="flex flex-col gap-0.5 flex-1 px-3 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200 ${
                  active
                    ? 'bg-accent/10 text-accent dark:bg-accent/15 dark:text-accent-light'
                    : 'text-muted hover:bg-cream-dark hover:text-ink dark:hover:bg-surface-dark-2 dark:hover:text-zinc-200'
                }`}
              >
                {active && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-accent dark:bg-accent-light rounded-r-full" />
                )}
                <Icon className="w-[18px] h-[18px]" strokeWidth={active ? 2 : 1.5} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="px-3 pb-4">
          <div className="rule mb-3" />
          <div className="flex items-center justify-between">
            <DarkModeToggle />
            <button
              onClick={logout}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-[13px] font-medium text-muted hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 transition-all"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden lg:inline">Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 backdrop-blur-xl bg-white/85 dark:bg-surface-dark/85 border-t border-border/60 dark:border-surface-dark-3/60 flex z-50 pb-[env(safe-area-inset-bottom)]">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex-1 flex flex-col items-center pt-2 pb-1.5 text-[10px] font-medium transition-colors ${
                active
                  ? 'text-accent dark:text-accent-light'
                  : 'text-muted'
              }`}
            >
              <Icon className="w-5 h-5 mb-0.5" strokeWidth={active ? 2 : 1.5} />
              <span>{item.label}</span>
              {active && (
                <div className="w-4 h-0.5 rounded-full bg-accent dark:bg-accent-light mt-0.5" />
              )}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
