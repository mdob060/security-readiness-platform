"use client";

import React from "react";
import { useAuth } from "@/lib/AuthContext";
import type { Role } from "@/lib/types";

/** Renders children only if the current user's role is included in `allow`. */
export function RoleGate({
  allow,
  children,
  fallback = null,
}: {
  allow: Role[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const { role } = useAuth();
  if (!role || !allow.includes(role)) return <>{fallback}</>;
  return <>{children}</>;
}
