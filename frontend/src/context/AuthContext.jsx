import { useState, useCallback } from 'react';
import { api, setAuthToken } from '../api';
import { AuthContext } from './auth-context';

const STORAGE_KEY = 'gradeai_auth';

function loadStoredAuth() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    const stored = loadStoredAuth();
    if (stored?.access_token) setAuthToken(stored.access_token);
    return stored;
  });

  const login = useCallback(async (username, password) => {
    const data = await api.login(username, password);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    setAuthToken(data.access_token);
    setAuth(data);
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setAuthToken(null);
    setAuth(null);
  }, []);

  const updateAuth = useCallback((patch) => {
    setAuth((prev) => {
      const next = { ...prev, ...patch };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const value = {
    user: auth,
    isAuthenticated: !!auth?.access_token,
    role: auth?.role,
    login,
    logout,
    updateAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
