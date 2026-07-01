"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface PollingOptions {
  intervalMs?: number;
  enabled?: boolean;
}

interface PollingResult<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refetch: () => void;
}

export function usePolling<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options: PollingOptions = {}
): PollingResult<T> {
  const { intervalMs = 10000, enabled = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);

  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  const load = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    (async () => {
      if (!cancelled) await load();
    })();
    const id = setInterval(load, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, intervalMs, load, ...deps]);

  return { data, error, loading, refetch: load };
}
