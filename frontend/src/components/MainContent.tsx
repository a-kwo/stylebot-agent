'use client';

import { useAuth } from '@/contexts/AuthContext';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

export default function MainContent({ children }: { children: React.ReactNode }) {
  const { authenticated } = useAuth();
  const pathname = usePathname();

  return (
    <main className={`${authenticated && pathname !== '/' && pathname !== '/login' ? 'md:ml-56' : ''} ${pathname === '/' || pathname === '/login' ? '' : 'pb-20 md:pb-0'}`}>
      <AnimatePresence mode="wait">
        <motion.div
          key={pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </main>
  );
}
