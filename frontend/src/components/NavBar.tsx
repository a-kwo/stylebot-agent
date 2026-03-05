'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import DarkModeToggle from './DarkModeToggle';

const navItems = [
  { href: '/chat', label: 'Chat', icon: 'M' },
  { href: '/wardrobe', label: 'Wardrobe', icon: 'W' },
  { href: '/builder', label: 'Builder', icon: 'B' },
  { href: '/outfits', label: 'Outfits', icon: 'O' },
  { href: '/profile', label: 'Profile', icon: 'P' },
];

export default function NavBar() {
  const pathname = usePathname();
  const { authenticated, logout } = useAuth();

  if (!authenticated) return null;

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-56 h-screen fixed left-0 top-0 bg-white dark:bg-zinc-900 border-r border-border dark:border-border-dark p-4">
        <div className="text-xl font-bold mb-8 tracking-tight">StyleBot</div>
        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                pathname === item.href
                  ? 'bg-ink text-cream dark:bg-cream dark:text-ink'
                  : 'text-muted hover:bg-zinc-100 dark:hover:bg-zinc-800'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center justify-between mt-auto pt-4 border-t border-border dark:border-border-dark">
          <DarkModeToggle />
          <button onClick={logout} className="btn-ghost text-sm text-red-500">
            Logout
          </button>
        </div>
      </aside>

      {/* Mobile bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-zinc-900 border-t border-border dark:border-border-dark flex z-50">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex-1 flex flex-col items-center py-3 text-xs font-medium transition-colors ${
              pathname === item.href
                ? 'text-ink dark:text-cream'
                : 'text-muted'
            }`}
          >
            <span className="text-lg mb-0.5">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </>
  );
}
