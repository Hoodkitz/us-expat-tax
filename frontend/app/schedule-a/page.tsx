"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiMe } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type FilingStatus = "single" | "married_filing_jointly" | "married_filing_separately";

interface ScheduleAFormState {
  adjusted_gross_income: string;
  medical_expenses: string;
  state_local_taxes: string;
  mortgage_interest: string;
  mortgage_debt: string;
  charitable_contributions: string;
  casualty_theft_losses: string;
  filing_status: FilingStatus;
}

interface ScheduleAResult {
  adjusted_gross_income: number;
  medical_expenses_deductible: number;
  salt_deductible: number;
  mortgage_interest_deductible: number;
  charitable_contributions_deductible: number;
  casualty_theft_losses_deductible: number;
  total_itemized_deductions: number;
  standard_deduction: number;
  recommended_deduction: number;
  use_itemized: boolean;
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

async function apiScheduleACalculate(data: {
  adjusted_gross_income: number;
  medical_expenses: number;
  state_local_taxes: number;
  mortgage_interest: number;
  mortgage_debt: number;
  charitable_contributions: number;
  casualty_theft_losses: number;
  filing_status: FilingStatus;
}): Promise<ScheduleAResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch("http://localhost:8000/api/v1/schedule-a/calculate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function ScheduleAPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);

  const [form, setForm] = useState<ScheduleAFormState>({
    adjusted_gross_income: "",
    medical_expenses: "",
    state_local_taxes: "",
    mortgage_interest: "",
    mortgage_debt: "",
    charitable_contributions: "",
    casualty_theft_losses: "",
    filing_status: "single",
  });
  const [result, setResult] = useState<ScheduleAResult | null>(null);
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

  async function handleCalculate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await apiScheduleACalculate({
        adjusted_gross_income: parseFloat(form.adjusted_gross_income) || 0,
        medical_expenses: parseFloat(form.medical_expenses) || 0,
        state_local_taxes: parseFloat(form.state_local_taxes) || 0,
        mortgage_interest: parseFloat(form.mortgage_interest) || 0,
        mortgage_debt: parseFloat(form.mortgage_debt) || 0,
        charitable_contributions: parseFloat(form.charitable_contributions) || 0,
        casualty_theft_losses: parseFloat(form.casualty_theft_losses) || 0,
        filing_status: form.filing_status,
      });
      setResult(data);
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
            <h1 className="text-2xl font-bold text-blue-400">Schedule A</h1>
            <p className="text-sm text-gray-400">Itemized Deductions Calculator</p>
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
              Calculate Itemized Deductions
            </h2>
            <p className="text-sm text-gray-400 mb-6">
              Calculate your Schedule A itemized deductions for tax year 2025.
              Medical expenses are deductible only above 7.5% of AGI, SALT is capped at $10,000,
              mortgage interest is deductible on up to $750,000 of debt, and charitable
              contributions are limited to 60% of AGI.
            </p>

            <form onSubmit={handleCalculate} className="space-y-4">
              {/* AGI */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Adjusted Gross Income (AGI) (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.adjusted_gross_income}
                  onChange={(e) =>
                    setForm({ ...form, adjusted_gross_income: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="85000.00"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Your Adjusted Gross Income from Form 1040, Line 11
                </p>
              </div>

              {/* Filing Status */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Filing Status
                </label>
                <select
                  value={form.filing_status}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      filing_status: e.target.value as FilingStatus,
                    })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="single">Single</option>
                  <option value="married_filing_jointly">Married Filing Jointly</option>
                  <option value="married_filing_separately">Married Filing Separately</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Affects SALT cap ($5,000 if MFS) and standard deduction amount
                </p>
              </div>

              {/* Medical Expenses */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Medical & Dental Expenses (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.medical_expenses}
                  onChange={(e) =>
                    setForm({ ...form, medical_expenses: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="5000.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Only expenses exceeding 7.5% of AGI are deductible
                </p>
              </div>

              {/* SALT */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  State & Local Taxes (SALT) (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.state_local_taxes}
                  onChange={(e) =>
                    setForm({ ...form, state_local_taxes: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="12000.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Capped at $10,000 ($5,000 if married filing separately)
                </p>
              </div>

              {/* Mortgage Interest */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Mortgage Interest Paid (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.mortgage_interest}
                  onChange={(e) =>
                    setForm({ ...form, mortgage_interest: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="8000.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  From Form 1098 (Mortgage Interest Statement)
                </p>
              </div>

              {/* Mortgage Debt */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Mortgage Debt Principal (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.mortgage_debt}
                  onChange={(e) =>
                    setForm({ ...form, mortgage_debt: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="400000.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Interest deductible on up to $750,000 of debt (post-2017)
                </p>
              </div>

              {/* Charitable Contributions */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Charitable Cash Contributions (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.charitable_contributions}
                  onChange={(e) =>
                    setForm({ ...form, charitable_contributions: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="3000.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Deductible up to 60% of AGI
                </p>
              </div>

              {/* Casualty/Theft Losses */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Casualty/Theft Losses (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={form.casualty_theft_losses}
                  onChange={(e) =>
                    setForm({ ...form, casualty_theft_losses: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Only losses from federally declared disasters are deductible
                </p>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Calculating..." : "Calculate Deductions"}
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
                  Itemized Deductions Breakdown
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="text-gray-400">Adjusted Gross Income:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.adjusted_gross_income)}
                  </div>

                  <div className="col-span-2 border-t border-gray-700 pt-2 mt-2"></div>

                  <div className="text-gray-400">Medical Expenses (over 7.5% AGI):</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.medical_expenses_deductible)}
                  </div>

                  <div className="text-gray-400">SALT (capped):</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.salt_deductible)}
                  </div>

                  <div className="text-gray-400">Mortgage Interest:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.mortgage_interest_deductible)}
                  </div>

                  <div className="text-gray-400">Charitable Contributions:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.charitable_contributions_deductible)}
                  </div>

                  <div className="text-gray-400">Casualty/Theft Losses:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.casualty_theft_losses_deductible)}
                  </div>

                  <div className="col-span-2 border-t border-gray-700 pt-2 mt-2"></div>

                  <div className="text-lg font-semibold text-gray-200">Total Itemized Deductions:</div>
                  <div className="text-right font-mono text-lg font-bold text-green-400">
                    {usd(result.total_itemized_deductions)}
                  </div>

                  <div className="text-gray-400">Standard Deduction:</div>
                  <div className="text-right font-mono text-gray-100">
                    {usd(result.standard_deduction)}
                  </div>

                  <div className="col-span-2 border-t border-gray-700 pt-2 mt-2"></div>

                  <div className="text-lg font-semibold text-gray-200">Recommended Deduction:</div>
                  <div className="text-right font-mono text-lg font-bold text-blue-400">
                    {usd(result.recommended_deduction)}
                  </div>

                  <div className="text-gray-400">Use Itemized:</div>
                  <div className="text-right font-mono text-gray-100">
                    {result.use_itemized ? "Yes ✓" : "No (use standard)"}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-4 border-t border-gray-700 pt-3">
                  <strong>Note:</strong> {result.use_itemized
                    ? "Your itemized deductions exceed the standard deduction. Use Schedule A."
                    : "Your standard deduction exceeds your itemized deductions. Use the standard deduction instead."}
                </p>
              </div>
            )}
          </div>

          {/* Info Box */}
          <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-300 mb-2">
              📘 About Schedule A
            </h3>
            <ul className="text-xs text-gray-300 space-y-1">
              <li>• Medical expenses: Only amount exceeding 7.5% of AGI is deductible (IRC §213)</li>
              <li>• SALT: State and local taxes capped at $10,000 ($5,000 if MFS) (IRC §164)</li>
              <li>• Mortgage interest: Deductible on up to $750,000 of debt (IRC §163(h))</li>
              <li>• Charitable contributions: Up to 60% of AGI for cash donations (IRC §170)</li>
              <li>• Casualty losses: Only federally declared disasters (IRC §165)</li>
              <li>• Standard deduction 2025: $15,000 single, $30,000 MFJ, $15,000 MFS</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}