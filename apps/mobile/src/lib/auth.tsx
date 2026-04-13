import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  clearToken,
  getToken,
  getUser,
  login as apiLogin,
  setOnUnauthorized,
  setToken,
  setUser as persistUser,
} from './api';

/**
 * AuthContext — holds the current user and exposes signIn / signOut.
 *
 * Used by the RootNavigator to decide whether to show the auth stack
 * (login screen) or the main app stack. The auth state rehydrates from
 * AsyncStorage on mount so the app remembers you between launches.
 */

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  agency_id: number;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Rehydrate on mount
  useEffect(() => {
    let mounted = true;
    (async () => {
      const token = await getToken();
      const storedUser = await getUser();
      if (mounted && token && storedUser) {
        setUser(storedUser);
      }
      if (mounted) setLoading(false);
    })();
    return () => {
      mounted = false;
    };
  }, []);

  // Register the 401 handler so api.ts can trigger sign-out
  useEffect(() => {
    setOnUnauthorized(() => {
      setUser(null);
    });
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      const response = await apiLogin(email, password);
      await setToken(response.access_token);
      await persistUser(response.user);
      setUser(response.user);
    } catch (e: any) {
      setError(e.message || 'Sign in failed');
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const signOut = useCallback(async () => {
    await clearToken();
    setUser(null);
  }, []);

  const value: AuthContextValue = {
    user,
    loading,
    error,
    isAuthenticated: user !== null,
    signIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside an AuthProvider');
  }
  return ctx;
}
