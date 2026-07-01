"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";

interface NavItem {
  label: string;
  href: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: "Overview",
    items: [{ label: "Dashboard", href: "/dashboard" }],
  },
  {
    title: "Offensive Operations",
    items: [
      { label: "Red Team", href: "/red-team" },
      { label: "Scan Scope", href: "/scan-scope" },
    ],
  },
  {
    title: "Defensive Operations",
    items: [
      { label: "Blue Team", href: "/blue-team" },
      { label: "Vulnerabilities", href: "/vulnerabilities" },
      { label: "PCI-DSS", href: "/pci-dss" },
    ],
  },
  {
    title: "Monitoring & Detection",
    items: [
      { label: "SOC Center", href: "/soc-center" },
      { label: "Honeypot", href: "/honeypot" },
      { label: "Incidents", href: "/incidents" },
      { label: "Sigma Rules", href: "/sigma-rules" },
      { label: "Threat Hunting", href: "/threat-hunting" },
    ],
  },
  {
    title: "Intelligence & Automation",
    items: [
      { label: "AI Brain", href: "/ai-brain" },
      { label: "Automation", href: "/automation" },
      { label: "Live Pipeline", href: "/live-pipeline" },
    ],
  },
  {
    title: "Threat Intelligence",
    items: [
      { label: "Threat Intel", href: "/threat-intel" },
      { label: "Federation", href: "/federation" },
    ],
  },
  {
    title: "Sector Modules",
    items: [
      { label: "Banking", href: "/banking" },
      { label: "OT/SCADA", href: "/ot-scada" },
      { label: "UEBA", href: "/ueba" },
      { label: "SWIFT CSP", href: "/swift-csp" },
      { label: "AML", href: "/aml" },
      { label: "Sector Monitor", href: "/sector-monitor" },
    ],
  },
  {
    title: "Management & Reporting",
    items: [
      { label: "GRC", href: "/grc" },
      { label: "Tenants", href: "/tenants" },
      { label: "Analytics", href: "/analytics" },
      { label: "Reports", href: "/reports" },
      { label: "Phishing Simulation", href: "/phishing" },
      { label: "Settings", href: "/settings" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { username, role, logout, isLoading, token } = useAuth();

  if (pathname === "/login") return null;
  if (isLoading || !token) return null;

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-[#1e2530] bg-[#0a0e14]">
      <div className="flex items-center gap-2 border-b border-[#1e2530] px-4 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-gradient-to-br from-blue-600 to-blue-800 text-lg font-bold text-white">
          د
        </div>
        <div>
          <div className="text-sm font-bold tracking-wide text-slate-100">
            DIR&apos;A <span className="text-slate-500">درع</span>
          </div>
          <div className="text-[10px] uppercase tracking-widest text-slate-500">
            Security Operations
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto scrollbar-thin px-2 py-3">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="mb-4">
            <div className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-slate-600">
              {group.title}
            </div>
            <div className="flex flex-col gap-0.5">
              {group.items.map((item) => {
                const active =
                  pathname === item.href || pathname?.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                      active
                        ? "bg-blue-600/15 text-blue-400 font-medium border-l-2 border-blue-500 -ml-0.5 pl-[11px]"
                        : "text-slate-400 hover:bg-[#11161d] hover:text-slate-200"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-[#1e2530] px-4 py-3">
        <div className="mb-2 flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-slate-200">
              {username}
            </div>
            <div className="text-[10px] uppercase tracking-wide text-slate-500">
              {role}
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full rounded-md border border-[#1e2530] bg-[#11161d] px-3 py-1.5 text-xs font-medium text-slate-300 hover:border-red-500/40 hover:text-red-400 transition-colors"
        >
          Logout
        </button>
      </div>
    </aside>
  );
}
