"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { apiClient, ApiError } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";
import { Button, Input, Label } from "@/components/Button";
import type { LoginResponse } from "@/lib/types";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiClient.post<LoginResponse>(
        "/api/auth/login",
        { username, password },
        { skipAuthRedirect: true }
      );
      login(res.access_token, res.role, res.username);
      router.replace("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0e14] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 text-2xl font-bold text-white shadow-lg shadow-blue-950/50">
            د
          </div>
          <h1 className="text-2xl font-bold tracking-wide text-slate-100">
            DIR&apos;A <span className="text-slate-500">درع</span>
          </h1>
          <p className="mt-1 text-xs uppercase tracking-widest text-slate-500">
            Security Operations Platform
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-lg border border-[#1e2530] bg-[#0d1117] p-6 shadow-xl"
        >
          <div className="mb-4">
            <Label>Username</Label>
            <Input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              autoFocus
              required
            />
          </div>
          <div className="mb-4">
            <Label>Password</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="mb-4 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full justify-center"
          >
            {loading ? "Signing in..." : "Sign In"}
          </Button>
        </form>

        <div className="mt-4 rounded-md border border-[#1e2530] bg-[#0d1117] px-4 py-3 text-xs text-slate-500">
          <span className="text-slate-400">Default seeded credentials: </span>
          <span className="mono text-slate-300">admin</span> /{" "}
          <span className="mono text-slate-300">ChangeMe123!</span>
        </div>
      </div>
    </div>
  );
}
