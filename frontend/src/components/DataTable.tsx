import React from "react";
import { Badge } from "./Badge";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  mono?: boolean;
  badge?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  keyField?: keyof T;
  emptyMessage?: string;
  loading?: boolean;
  error?: string | null;
  onRowClick?: (row: T) => void;
}

function getValue<T>(row: T, key: string): unknown {
  return (row as Record<string, unknown>)[key];
}

export function DataTable<T>({
  columns,
  rows,
  keyField,
  emptyMessage = "No data available.",
  loading,
  error,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="w-full min-w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-[#1e2530] text-left">
            {columns.map((col) => (
              <th
                key={col.key}
                style={col.width ? { width: col.width } : undefined}
                className="whitespace-nowrap px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-6 text-center text-slate-500"
              >
                Loading...
              </td>
            </tr>
          )}
          {!loading && error && (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-6 text-center text-red-400"
              >
                {error}
              </td>
            </tr>
          )}
          {!loading && !error && rows.length === 0 && (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-6 text-center text-slate-500"
              >
                {emptyMessage}
              </td>
            </tr>
          )}
          {!loading &&
            !error &&
            rows.map((row, idx) => (
              <tr
                key={keyField ? String(getValue(row, keyField as string)) : idx}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`border-b border-[#151b23] ${
                  onRowClick ? "cursor-pointer hover:bg-[#11161d]" : ""
                }`}
              >
                {columns.map((col) => {
                  const raw = col.render ? col.render(row) : getValue(row, col.key);
                  return (
                    <td
                      key={col.key}
                      className={`px-3 py-2 align-middle text-slate-300 ${
                        col.mono ? "mono text-xs" : ""
                      }`}
                    >
                      {col.badge ? (
                        <Badge variant={String(raw)}>{String(raw)}</Badge>
                      ) : (
                        (raw as React.ReactNode) ?? (
                          <span className="text-slate-600">—</span>
                        )
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
