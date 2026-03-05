'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import { isAuthenticated, clearToken, getOnboardingStatus } from '@/lib/api';

interface AuthState {
  authenticated: boolean;
  onboarded: boolean | null; // null = loading
  loading: boolean;          // true until initial auth check completes
  logout: () => void;
  refresh: () => void;
}

const AuthContext = createContext<AuthState>({
  authenticated: false,
  onboarded: null,
  loading: true,
  logout: () => {},
  refresh: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [onboarded, setOnboarded] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  const check = async () => {
    const authed = isAuthenticated();
    setAuthenticated(authed);
    if (authed) {
      try {
        const status = await getOnboardingStatus();
        setOnboarded(status);
      } catch {
        setOnboarded(false);
      }
    } else {
      setOnboarded(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    check();
  }, []);

  const logout = () => {
    clearToken();
    setAuthenticated(false);
    setOnboarded(null);
  };

  return (
    <AuthContext.Provider
      value={{ authenticated, onboarded, loading, logout, refresh: check }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
