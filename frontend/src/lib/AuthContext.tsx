"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import type { Role } from "./types";

interface AuthState {
  token: string | null;
  role: Role | null;
  username: string | null;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (token: string, role: Role, username: string) => void;
  logout: () => void;
  isAdmin: boolean;
  isAnalystOrAbove: boolean;
  isViewer: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const PUBLIC_ROUTES = ["/login"];

function readAuthFromStorage(): AuthState {
  if (typeof window === "undefined") {
    return { token: null, role: null, username: null, isLoading: true };
  }
  return {
    token: localStorage.getItem("dira_token"),
    role: localStorage.getItem("dira_role") as Role | null,
    username: localStorage.getItem("dira_username"),
    isLoading: false,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(readAuthFromStorage);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!state.token && !PUBLIC_ROUTES.includes(pathname)) {
      router.replace("/login");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, state.token]);

  const login = useCallback((token: string, role: Role, username: string) => {
    localStorage.setItem("dira_token", token);
    localStorage.setItem("dira_role", role);
    localStorage.setItem("dira_username", username);
    setState({ token, role, username, isLoading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("dira_token");
    localStorage.removeItem("dira_role");
    localStorage.removeItem("dira_username");
    setState({ token: null, role: null, username: null, isLoading: false });
    router.replace("/login");
  }, [router]);

  const value: AuthContextValue = {
    ...state,
    login,
    logout,
    isAdmin: state.role === "admin",
    isAnalystOrAbove: state.role === "admin" || state.role === "analyst",
    isViewer: state.role === "viewer",
  };

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
