import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi, getToken, setToken, setUnauthorizedHandler } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  const loadUser = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const { data } = await authApi.me();
      setUser(data);
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setToken(null);
      setUser(null);
    });
    loadUser();
  }, [loadUser]);

  const login = useCallback(async (email, password) => {
    const { data } = await authApi.login({ email, password });
    setToken(data.access_token);
    const me = await authApi.me();
    setUser(me.data);
    return me.data;
  }, []);

  const register = useCallback(async (payload) => {
    const { data } = await authApi.register(payload);
    setToken(data.access_token);
    const me = await authApi.me();
    setUser(me.data);
    return me.data;
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refresh: loadUser, isAuthenticated: !!user }),
    [user, loading, login, register, logout, loadUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
