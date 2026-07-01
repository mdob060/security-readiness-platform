"use client";

import { useState } from "react";
import { PageShell } from "@/components/PageShell";
import { Card } from "@/components/Card";
import { DataTable, Column } from "@/components/DataTable";
import { Badge } from "@/components/Badge";
import { Button, Input, Label, Select } from "@/components/Button";
import { useAuth } from "@/lib/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import { apiClient, ApiError } from "@/lib/apiClient";

interface Transaction {
  id: number;
  account_from: string;
  account_to: string;
  amount: number;
  currency: string;
  channel: string;
  risk_score: number;
  created_at: string;
}

interface FraudAlert {
  id: number;
  transaction_id: number;
  reason: string;
  severity: string;
  created_at: string;
}

function riskVariant(score: number): string {
  if (score >= 75) return "critical";
  if (score >= 50) return "high";
  if (score >= 25) return "medium";
  return "low";
}

const CHANNELS = ["atm", "wire", "card", "mobile"];

export default function BankingPage() {
  const { isAnalystOrAbove } = useAuth();

  const {
    data: transactions,
    loading: txLoading,
    error: txError,
    refetch: refetchTx,
  } = usePolling<Transaction[]>(
    () => apiClient.get<Transaction[]>("/api/banking/transactions"),
    []
  );

  const {
    data: alerts,
    loading: alertsLoading,
    error: alertsError,
    refetch: refetchAlerts,
  } = usePolling<FraudAlert[]>(
    () => apiClient.get<FraudAlert[]>("/api/banking/fraud-alerts"),
    []
  );

  const [form, setForm] = useState({
    account_from: "",
    account_to: "",
    amount: "",
    currency: "USD",
    channel: "wire",
  });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const txColumns: Column<Transaction>[] = [
    { key: "account_from", header: "From", mono: true },
    { key: "account_to", header: "To", mono: true },
    {
      key: "amount",
      header: "Amount",
      render: (row) =>
        `${row.amount.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })} ${row.currency}`,
    },
    { key: "channel", header: "Channel" },
    {
      key: "risk_score",
      header: "Risk Score",
      render: (row) => (
        <Badge variant={riskVariant(row.risk_score)}>
          {row.risk_score.toFixed(0)}
        </Badge>
      ),
    },
    {
      key: "created_at",
      header: "Created",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  const alertColumns: Column<FraudAlert>[] = [
    { key: "transaction_id", header: "Txn ID", mono: true },
    { key: "reason", header: "Reason" },
    { key: "severity", header: "Severity", badge: true },
    {
      key: "created_at",
      header: "Created",
      mono: true,
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSuccessMsg(null);
    const amountNum = Number(form.amount);
    if (!form.account_from || !form.account_to || !form.amount || Number.isNaN(amountNum)) {
      setFormError("Please fill in all required fields with valid values.");
      return;
    }
    setSubmitting(true);
    try {
      const created = await apiClient.post<Transaction>("/api/banking/transactions", {
        account_from: form.account_from,
        account_to: form.account_to,
        amount: amountNum,
        currency: form.currency || "USD",
        channel: form.channel,
      });
      setSuccessMsg(
        `Transaction #${created.id} submitted (risk score: ${created.risk_score.toFixed(0)}).`
      );
      setForm({ account_from: "", account_to: "", amount: "", currency: "USD", channel: "wire" });
      refetchTx();
      refetchAlerts();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to submit transaction.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell
      title="Banking"
      description="Transaction monitoring and fraud alerts"
    >
      <div className="flex flex-col gap-6">
        {isAnalystOrAbove && (
          <Card title="Submit Test Transaction">
            <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <div>
                <Label>Account From</Label>
                <Input
                  value={form.account_from}
                  onChange={(e) => setForm({ ...form, account_from: e.target.value })}
                  placeholder="ACC1"
                  required
                />
              </div>
              <div>
                <Label>Account To</Label>
                <Input
                  value={form.account_to}
                  onChange={(e) => setForm({ ...form, account_to: e.target.value })}
                  placeholder="ACC2"
                  required
                />
              </div>
              <div>
                <Label>Amount</Label>
                <Input
                  type="number"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                  placeholder="1000.00"
                  required
                />
              </div>
              <div>
                <Label>Currency</Label>
                <Input
                  value={form.currency}
                  onChange={(e) => setForm({ ...form, currency: e.target.value })}
                  placeholder="USD"
                />
              </div>
              <div>
                <Label>Channel</Label>
                <Select
                  value={form.channel}
                  onChange={(e) => setForm({ ...form, channel: e.target.value })}
                >
                  {CHANNELS.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="col-span-full flex items-center gap-3">
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Submitting..." : "Submit Transaction"}
                </Button>
                {formError && <span className="text-sm text-red-400">{formError}</span>}
                {successMsg && <span className="text-sm text-green-400">{successMsg}</span>}
              </div>
            </form>
          </Card>
        )}

        <Card title="Transactions">
          <DataTable
            columns={txColumns}
            rows={transactions ?? []}
            keyField="id"
            loading={txLoading}
            error={txError}
            emptyMessage="No transactions recorded yet."
          />
        </Card>

        <Card title="Fraud Alerts">
          <DataTable
            columns={alertColumns}
            rows={alerts ?? []}
            keyField="id"
            loading={alertsLoading}
            error={alertsError}
            emptyMessage="No fraud alerts."
          />
        </Card>
      </div>
    </PageShell>
  );
}
