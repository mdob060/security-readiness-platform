"use client";

import React from "react";
import { useAuth } from "@/lib/AuthContext";

export function PageShell({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="ml-64 flex min-h-screen items-center justify-center text-slate-500">
        Loading...
      </div>
    );
  }

  if (!token) {
    return (
      <div className="ml-64 flex min-h-screen items-center justify-center text-slate-500">
        Redirecting to login...
      </div>
    );
  }

  return (
    <div className="ml-64 min-h-screen">
      <header className="sticky top-0 z-30 border-b border-[#1e2530] bg-[#0a0e14]/95 px-6 py-4 backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-100">{title}</h1>
            {description && (
              <p className="mt-0.5 text-sm text-slate-500">{description}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      </header>
      <main className="p-6">{children}</main>
    </div>
  );
}
