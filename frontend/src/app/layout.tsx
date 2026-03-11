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
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap"
          rel="stylesheet"
        />
        <meta name="theme-color" content="#faf9f7" />
      </head>
      <body className="min-h-screen noise">
        <AuthProvider>
          <NavBar />
          <MainContent>{children}</MainContent>
        </AuthProvider>
      </body>
    </html>
  );
}
