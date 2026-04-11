"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import {
  getToken,
  setToken,
  clearToken,
  getMe,
  type UserInfo,
} from "../lib/api";

interface AuthContextType {
  user: UserInfo | null;
  loading: boolean;
  login: (token: string) => void;
  logout: () => void;
  refresh: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: () => {},
  logout: () => {},
  refresh: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    let token = getToken();
    // Auto dev-login if no token (dev mode only)
    if (!token) {
      try {
        const resp = await fetch("/api/auth/dev-login");
        const data = await resp.json();
        if (data.token) {
          setToken(data.token);
          token = data.token;
        }
      } catch {
        // Dev login not available (production)
      }
    }
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const info = await getMe();
      if (info.authenticated) {
        setUser(info);
      } else {
        clearToken();
        setUser(null);
      }
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Check for token in URL (from WeChat callback redirect)
    const params = new URLSearchParams(window.location.search);
    const tokenParam = params.get("token");
    if (tokenParam) {
      setToken(tokenParam);
      window.history.replaceState({}, "", window.location.pathname);
    }
    fetchUser();
  }, [fetchUser]);

  const login = (token: string) => {
    setToken(token);
    fetchUser();
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
