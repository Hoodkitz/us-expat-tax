"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiMe } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type FilingStatus =
  | "single"
  | "married_filing_jointly"
  | "married_filing_separately"
  | "head_of_household"
  | "qualifying_widow";

interface ScheduleRFormState {
  filing_status: FilingStatus;
  age: string;
  spouse_age: string;
  is_disabled: boolean;
  spouse_is_disabled: boolean;
  agi: string;
  nontaxable_social_security: string;
  nontaxable_pension: string;
  nontaxable_other: string;
  tax_year: number;
}

interface ScheduleRResult {
  filing_status: string;
  base_amount: number;
  total_nontaxable_income: number;
  agi_threshold: number;
  excess_agi: number;
  agi_reduction: number;
  total_reduction: number;
  credit_before_rate: number;
  credit_rate: number;
  credit_amount: number;
  eligible: boolean;
  explanation: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function usd(n: number) {
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("jwt_token");
}

async function apiScheduleRCalculate(data: {
  filing_status: FilingStatus;
  age: number;
  spouse_age: number | null;
  is_disabled: boolean;
  spouse_is_disabled: boolean;
  agi: number;
  nontaxable_social_security: number;
  nontaxable_pension: number;
  nontaxable_other: number;
  tax_year: number;
}): Promise<ScheduleRResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/schedule-r/calculate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function ScheduleRPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);

  const [form, setForm] = useState<ScheduleRFormState>({
    filing_status: "single",
    age: "",
    spouse_age: "",
    is_disabled: false,
    spouse_is_disabled: false,
    agi: "",
    nontaxable_social_security: "",
    nontaxable_pension: "",
    nontaxable_other: "",
    tax_year: 2025,
  });
  const [result, setResult] = useState<ScheduleRResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Auth guard
  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }
    apiMe()
      .then(() => setAuthReady(true))
      .catch(() => {
        localStorage.removeItem("jwt_token");
        router.replace("/auth/login");
      });
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const result = await apiScheduleRCalculate({
        filing_status: form.filing_status,
        age: parseInt(form.age) || 0,
        spouse_age: form.spouse_age ? parseInt(form.spouse_age) : null,
        is_disabled: form.is_disabled,
        spouse_is_disabled: form.spouse_is_disabled,
        agi: parseFloat(form.agi) || 0,
        nontaxable_social_security: parseFloat(form.nontaxable_social_security) || 0,
        nontaxable_pension: parseFloat(form.nontaxable_pension) || 0,
        nontaxable_other: parseFloat(form.nontaxable_other) || 0,
        tax_year: form.tax_year,
      });
      setResult(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  if (!authReady) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-400 text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-blue-400">Schedule R</h1>
            <p className="text-sm text-gray-400">Credit for the Elderly or the Disabled</p>
          </div>
          <Link
            href="/dashboard"
            className="text-sm text-blue-400 hover:text-blue-300 transition"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-100">
              Calculate Credit for the Elderly or Disabled
            </h2>
            <p className="text-sm text-gray-400 mb-6">
              Calculate your Schedule R credit based on age (65+), disability status,
              filing status, AGI, and nontaxable income. Uses 2025 tax rules: base amounts
              of $5,000 (single) to $7,500 (MFJ both 65+), reduced by 50% of AGI over
              threshold and nontaxable income, then multiplied by 15%.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Filing Status */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Filing Status
                </label>
                <select
                  value={form.filing_status}
                  onChange={(e) =>
                    setForm({ ...form, filing_status: e.target.value as FilingStatus })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="single">Single</option>
                  <option value="married_filing_jointly">Married Filing Jointly</option>
                  <option value="married_filing_separately">Married Filing Separately</option>
                  <option value="head_of_household">Head of Household</option>
                  <option value="qualifying_widow">Qualifying Widow(er)</option>
                </select>
              </div>

              {/* Age and Spouse Age */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Taxpayer Age
                  </label>
                  <input
                    type="number"
                    value={form.age}
                    onChange={(e) => setForm({ ...form, age: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="67"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Must be 65+ or permanently disabled
                  </p>
                </div>
                {form.filing_status === "married_filing_jointly" && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Spouse Age
                    </label>
                    <input
                      type="number"
                      value={form.spouse_age}
                      onChange={(e) => setForm({ ...form, spouse_age: e.target.value })}
                      className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="65"
                    />
                  </div>
                )}
              </div>

              {/* Disability Checkboxes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={form.is_disabled}
                    onChange={(e) => setForm({ ...form, is_disabled: e.target.checked })}
                    className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-700 rounded focus:ring-blue-500"
                  />
                  <label className="ml-2 text-sm text-gray-300">
                    Permanently and totally disabled
                  </label>
                </div>
                {form.filing_status === "married_filing_jointly" && (
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={form.spouse_is_disabled}
                      onChange={(e) =>
                        setForm({ ...form, spouse_is_disabled: e.target.checked })
                      }
                      className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-700 rounded focus:ring-blue-500"
                    />
                    <label className="ml-2 text-sm text-gray-300">
                      Spouse permanently and totally disabled
                    </label>
                  </div>
                )}
              </div>

              {/* AGI */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Adjusted Gross Income (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.agi}
                  onChange={(e) => setForm({ ...form, agi: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="12000.00"
                  required
                />
              </div>

              {/* Nontaxable Income */}
              <div className="border-t border-gray-700 pt-4">
                <h3 className="text-sm font-medium text-gray-300 mb-3">
                  Nontaxable Income (reduces credit)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Nontaxable Social Security
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={form.nontaxable_social_security}
                      onChange={(e) =>
                        setForm({ ...form, nontaxable_social_security: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Nontaxable Pension
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={form.nontaxable_pension}
                      onChange={(e) =>
                        setForm({ ...form, nontaxable_pension: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">
                      Other Nontaxable Income
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={form.nontaxable_other}
                      onChange={(e) =>
                        setForm({ ...form, nontaxable_other: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                </div>
              </div>

              {/* Tax Year */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Tax Year
                </label>
                <input
                  type="number"
                  value={form.tax_year}
                  onChange={(e) =>
                    setForm({ ...form, tax_year: parseInt(e.target.value) || 2025 })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min={2025}
                  max={2025}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Only 2025 supported currently</p>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Calculating..." : "Calculate Credit"}
              </button>
            </form>

            {/* Error */}
            {error && (
              <div className="mt-4 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            )}

            {/* Results */}
            {result && (
              <div className="mt-6 p-6 bg-gray-800 border border-gray-700 rounded-lg space-y-3">
                <h3 className="text-lg font-semibold text-green-400 mb-4">
                  Schedule R Credit Calculation
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="text-gray-400">Eligible:</div>
                  <div className="text-right font-mono text-gray-100">
                    {result.eligible ? "Yes" : "No"}
                  </div>

                  <div className="text-gray-400">Base Amount:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.base_amount)}
                  </div>

                  <div className="text-gray-400">Nontaxable Income:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.total_nontaxable_income)}
                  </div>

                  <div className="text-gray-400">AGI Threshold:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.agi_threshold)}
                  </div>

                  <div className="text-gray-400">Excess AGI:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.excess_agi)}
                  </div>

                  <div className="text-gray-400">AGI Reduction (50%):</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.agi_reduction)}
                  </div>

                  <div className="col-span-2 border-t border-gray-700 pt-2 mt-2"></div>

                  <div className="text-gray-400">Credit Before Rate:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.credit_before_rate)}
                  </div>

                  <div className="text-gray-400">Credit Rate:</div>
                  <div className="text-right font-mono text-gray-100">
                    {(result.credit_rate * 100).toFixed(0)}%
                  </div>

                  <div className="col-span-2 border-t border-gray-700 pt-2 mt-2"></div>

                  <div className="text-lg font-semibold text-gray-200">Credit Amount:</div>
                  <div className="text-right font-mono text-lg font-bold text-green-400">
                    {usd(result.credit_amount)}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-4 border-t border-gray-700 pt-3">
                  <strong>Calculation:</strong> {result.explanation}
                </p>
              </div>
            )}
          </div>

          {/* Info Box */}
          <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-300 mb-2">
              📘 About Schedule R
            </h3>
            <ul className="text-xs text-gray-300 space-y-1">
              <li>• Credit for taxpayers age 65+ or permanently and totally disabled</li>
              <li>• Base amounts: $5,000 (single), $7,500 (MFJ both 65+), $3,750 (MFS)</li>
              <li>• Reduced by 50% of AGI over $7,500 (single) or $10,000 (MFJ)</li>
              <li>• Also reduced by nontaxable Social Security and pensions</li>
              <li>• Final credit = 15% of remaining amount</li>
              <li>• Nonrefundable — can only reduce tax liability to zero</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
