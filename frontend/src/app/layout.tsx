import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/AuthContext";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Dir'a | Security Operations Platform",
  description: "Unified Security Operations Platform - درع",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className="min-h-full bg-[#0a0e14] text-slate-200 antialiased">
        <AuthProvider>
          <Sidebar />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
