"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CalculationEntry {
  id: string;
  timestamp: string;
  recommended_path: string | null;
  income_usd: string;
}

interface TaxSummaryOverview {
  tenant_id: string;
  total_calculations: number;
  total_income_usd: string;
  total_tax_paid_usd: string;
  total_us_tax_liability_usd: string;
  recommended_path: string | null;
  last_calculation: {
    id: string;
    timestamp: string;
    recommended_path: string | null;
  } | null;
  calculations: CalculationEntry[];
}

interface ExportResponse {
  export_id: string;
  file_path: string;
  summary: TaxSummaryOverview;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function fmtUSD(val: string | undefined): string {
  if (!val) return "–";
  const num = parseFloat(val);
  if (isNaN(num)) return val;
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(num);
}

function fmtDate(iso: string | undefined): string {
  if (!iso) return "–";
  try {
    return new Date(iso).toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function TaxSummaryPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<TaxSummaryOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }

    fetch(`${API_BASE}/api/v1/tax-summary/overview`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (res.status === 401 || res.status === 403) {
          localStorage.removeItem("jwt_token");
          router.replace("/auth/login");
          return;
        }
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail ?? `HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data: TaxSummaryOverview | undefined) => {
        if (data) setSummary(data);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unbekannter Fehler");
      })
      .finally(() => setLoading(false));
  }, [router]);

  async function handleExport() {
    const token = localStorage.getItem("jwt_token");
    if (!token) return;

    setExporting(true);
    setError(null);
    setExportSuccess(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/tax-summary/export`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ format: "json" }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `HTTP ${res.status}`);
      }

      const data: ExportResponse = await res.json();
      setExportSuccess(`Export erfolgreich: ${data.file_path}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Export fehlgeschlagen");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <span className="font-extrabold text-brand-800 text-lg">
          🇺🇸 US Expat Tax
        </span>
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="text-sm text-brand-600 hover:underline"
          >
            Dashboard
          </Link>
          <Link
            href="/history"
            className="text-sm text-brand-600 hover:underline"
          >
            Verlauf
          </Link>
          <Link
            href="/auth/logout"
            className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Abmelden
          </Link>
        </div>
      </nav>

      <main className="mx-auto max-w-5xl px-4 py-10">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800">
            Tax Summary
          </h1>
          <button
            onClick={handleExport}
            disabled={exporting || !summary || summary.total_calculations === 0}
            className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {exporting ? "Exportiere…" : "📥 JSON Export"}
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-16 text-gray-500">
            <span className="animate-pulse">Wird geladen …</span>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            Fehler: {error}
          </div>
        )}

        {/* Export Success */}
        {!loading && exportSuccess && (
          <div className="rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700 mb-4">
            ✅ {exportSuccess}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && summary && summary.total_calculations === 0 && (
          <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-12 text-center">
            <p className="text-gray-500 text-sm">
              Noch keine Berechnungen gespeichert.
            </p>
            <Link
              href="/dashboard"
              className="mt-4 inline-block rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700 transition-colors"
            >
              Zur Steuerberechnung
            </Link>
          </div>
        )}

        {/* Summary Cards */}
        {!loading && !error && summary && summary.total_calculations > 0 && (
          <div className="space-y-6">
            {/* Top Stats */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <p className="text-sm text-gray-500 mb-1">Berechnungen</p>
                <p className="text-2xl font-bold text-gray-800">
                  {summary.total_calculations}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <p className="text-sm text-gray-500 mb-1">Gesamteinkommen</p>
                <p className="text-2xl font-bold text-gray-800">
                  {fmtUSD(summary.total_income_usd)}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <p className="text-sm text-gray-500 mb-1">Gezahlte Steuern</p>
                <p className="text-2xl font-bold text-gray-800">
                  {fmtUSD(summary.total_tax_paid_usd)}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <p className="text-sm text-gray-500 mb-1">US-Steuerpflicht</p>
                <p className="text-2xl font-bold text-gray-800">
                  {fmtUSD(summary.total_us_tax_liability_usd)}
                </p>
              </div>
            </div>

            {/* Recommendation */}
            {summary.recommended_path && (
              <div className="rounded-2xl border border-brand-200 bg-brand-50 p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-brand-800 mb-2">
                  Empfohlene Strategie
                </h2>
                <div className="flex items-center gap-3">
                  <span className="inline-block rounded-full bg-brand-600 px-4 py-1.5 text-sm font-semibold text-white">
                    {summary.recommended_path}
                  </span>
                  <span className="text-sm text-brand-700">
                    {summary.recommended_path === "FTC"
                      ? "Foreign Tax Credit – ausländische Steuern werden angerechnet"
                      : "Foreign Earned Income Exclusion – bis $126.500 steuerfrei"}
                  </span>
                </div>
              </div>
            )}

            {/* Last Calculation */}
            {summary.last_calculation && (
              <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-800 mb-3">
                  Letzte Berechnung
                </h2>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div>
                    <p className="text-xs text-gray-500">Datum</p>
                    <p className="text-sm font-medium text-gray-800">
                      {fmtDate(summary.last_calculation.timestamp)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Strategie</p>
                    <p className="text-sm font-medium text-gray-800">
                      {summary.last_calculation.recommended_path ?? "–"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">ID</p>
                    <p className="text-sm font-medium text-gray-800 font-mono">
                      {summary.last_calculation.id.slice(0, 8)}…
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Calculations Table */}
            <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
                <h2 className="text-lg font-semibold text-gray-800">
                  Alle Berechnungen
                </h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-left">
                    <th className="px-5 py-3 font-semibold text-gray-600">
                      Datum
                    </th>
                    <th className="px-5 py-3 font-semibold text-gray-600">
                      Einkommen
                    </th>
                    <th className="px-5 py-3 font-semibold text-gray-600">
                      Strategie
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {summary.calculations.map((calc) => (
                    <tr
                      key={calc.id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-5 py-3 text-gray-700">
                        {fmtDate(calc.timestamp)}
                      </td>
                      <td className="px-5 py-3 text-gray-700">
                        {fmtUSD(calc.income_usd)}
                      </td>
                      <td className="px-5 py-3">
                        {calc.recommended_path ? (
                          <span
                            className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                              calc.recommended_path === "FTC"
                                ? "bg-blue-100 text-blue-700"
                                : "bg-green-100 text-green-700"
                            }`}
                          >
                            {calc.recommended_path}
                          </span>
                        ) : (
                          <span className="text-gray-400">–</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
