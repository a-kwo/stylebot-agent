'use client';

import { useAuth } from '@/contexts/AuthContext';

export default function MainContent({ children }: { children: React.ReactNode }) {
  const { authenticated } = useAuth();

  return (
    <main className={`${authenticated ? 'md:ml-56' : ''} pb-20 md:pb-0`}>
      {children}
    </main>
  );
}
