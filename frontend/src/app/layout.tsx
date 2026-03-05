import type { Metadata } from 'next';
import { AuthProvider } from '@/contexts/AuthContext';
import NavBar from '@/components/NavBar';
import MainContent from '@/components/MainContent';
import './globals.css';

export const metadata: Metadata = {
  title: 'StyleBot',
  description: 'Your AI styling assistant',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen">
        <AuthProvider>
          <NavBar />
          <MainContent>{children}</MainContent>
        </AuthProvider>
      </body>
    </html>
  );
}
