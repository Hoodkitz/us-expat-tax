"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface HistoryEntry {
  id: string;
  tenant_id: string;
  timestamp: string;
  input_data: {
    foreign_earned_income_usd?: string;
    [key: string]: unknown;
  };
  result_data: {
    recommended_path?: string;
    ftc?: { resulting_tax_usd?: string };
    feie?: { resulting_tax_usd?: string };
    [key: string]: unknown;
  };
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

function fmtDate(iso: string): string {
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

export default function HistoryPage() {
  const router = useRouter();
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }

    fetch(`${API_BASE}/api/v1/history`, {
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
      .then((data: HistoryEntry[] | undefined) => {
        if (data) setEntries(data);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unbekannter Fehler");
      })
      .finally(() => setLoading(false));
  }, [router]);

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
            href="/auth/logout"
            className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Abmelden
          </Link>
        </div>
      </nav>

      <main className="mx-auto max-w-5xl px-4 py-10">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">
          Berechnungshistorie
        </h1>

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

        {/* Empty State */}
        {!loading && !error && entries.length === 0 && (
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

        {/* Table */}
        {!loading && !error && entries.length > 0 && (
          <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
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
                  <th className="px-5 py-3 font-semibold text-gray-600">
                    Ergebnis (verbleibende US-Steuer)
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {entries.map((entry) => {
                  const path = entry.result_data.recommended_path ?? "–";
                  const resultingTax =
                    path === "FTC"
                      ? entry.result_data.ftc?.resulting_tax_usd
                      : entry.result_data.feie?.resulting_tax_usd;

                  return (
                    <tr
                      key={entry.id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-5 py-3 text-gray-700">
                        {fmtDate(entry.timestamp)}
                      </td>
                      <td className="px-5 py-3 text-gray-700">
                        {fmtUSD(entry.input_data.foreign_earned_income_usd)}
                      </td>
                      <td className="px-5 py-3">
                        <span
                          className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                            path === "FTC"
                              ? "bg-blue-100 text-blue-700"
                              : "bg-green-100 text-green-700"
                          }`}
                        >
                          {path}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-medium text-gray-800">
                        {fmtUSD(resultingTax)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
