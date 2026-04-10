import React, { createContext, useState, useCallback, ReactNode } from 'react';
import { User } from '../../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isAuthenticated: false,
  login: async () => {},
  logout: async () => {},
});

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const isAuthenticated = !!token && !!user;

  const login = useCallback(async (email: string, _password: string) => {
    // Mock login implementation
    // In production, this would call the API and store token in SecureStore
    const mockUser: User = {
      id: '1',
      email,
      firstName: 'John',
      lastName: 'Doe',
      role: 'employee',
      department: 'Engineering',
    };
    const mockToken = 'mock-jwt-token-' + Date.now();

    setUser(mockUser);
    setToken(mockToken);

    // Would store token: await SecureStore.setItemAsync('auth_token', mockToken);
  }, []);

  const logout = useCallback(async () => {
    setUser(null);
    setToken(null);
    // Would clear token: await SecureStore.deleteItemAsync('auth_token');
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
