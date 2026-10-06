"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiMe } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type FilingStatus = "single" | "married_filing_jointly" | "married_filing_separately";
type ActiveTab = "calculator" | "deduction";

interface ScheduleSEFormState {
  net_self_employment_income: string;
  filing_status: FilingStatus;
  tax_year: number;
}

interface ScheduleSEResult {
  net_self_employment_income: number;
  net_earnings_subject_to_se_tax: number;
  social_security_tax: number;
  medicare_tax: number;
  additional_medicare_tax: number;
  total_self_employment_tax: number;
  deductible_se_tax: number;
}

interface SEDeductionState {
  total_self_employment_tax: string;
}

interface SEDeductionResult {
  total_self_employment_tax: number;
  deductible_se_tax: number;
  description: string;
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

async function apiScheduleSECalculate(data: {
  net_self_employment_income: number;
  filing_status: FilingStatus;
  tax_year: number;
}): Promise<ScheduleSEResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch("http://localhost:8000/api/v1/schedule-se/calculate", {
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

async function apiScheduleSEDeduction(data: {
  total_self_employment_tax: number;
}): Promise<SEDeductionResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch("http://localhost:8000/api/v1/schedule-se/deduction", {
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
export default function ScheduleSEPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>("calculator");

  // Calculator state
  const [calculatorForm, setCalculatorForm] = useState<ScheduleSEFormState>({
    net_self_employment_income: "",
    filing_status: "single",
    tax_year: 2025,
  });
  const [calculatorResult, setCalculatorResult] = useState<ScheduleSEResult | null>(null);
  const [calculatorError, setCalculatorError] = useState<string | null>(null);
  const [calculatorLoading, setCalculatorLoading] = useState(false);

  // Deduction state
  const [deductionForm, setDeductionForm] = useState<SEDeductionState>({
    total_self_employment_tax: "",
  });
  const [deductionResult, setDeductionResult] = useState<SEDeductionResult | null>(null);
  const [deductionError, setDeductionError] = useState<string | null>(null);
  const [deductionLoading, setDeductionLoading] = useState(false);

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

  // Calculator handlers
  async function handleCalculate(e: React.FormEvent) {
    e.preventDefault();
    setCalculatorError(null);
    setCalculatorResult(null);
    setCalculatorLoading(true);
    try {
      const result = await apiScheduleSECalculate({
        net_self_employment_income: parseFloat(calculatorForm.net_self_employment_income) || 0,
        filing_status: calculatorForm.filing_status,
        tax_year: calculatorForm.tax_year,
      });
      setCalculatorResult(result);
    } catch (err: unknown) {
      setCalculatorError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setCalculatorLoading(false);
    }
  }

  // Deduction handlers
  async function handleDeduction(e: React.FormEvent) {
    e.preventDefault();
    setDeductionError(null);
    setDeductionResult(null);
    setDeductionLoading(true);
    try {
      const result = await apiScheduleSEDeduction({
        total_self_employment_tax: parseFloat(deductionForm.total_self_employment_tax) || 0,
      });
      setDeductionResult(result);
    } catch (err: unknown) {
      setDeductionError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setDeductionLoading(false);
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
            <h1 className="text-2xl font-bold text-blue-400">Schedule SE</h1>
            <p className="text-sm text-gray-400">Self-Employment Tax Calculator</p>
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
        {/* Tabs */}
        <div className="flex space-x-1 mb-6 border-b border-gray-800">
          <button
            onClick={() => setActiveTab("calculator")}
            className={`px-6 py-3 text-sm font-medium transition border-b-2 ${
              activeTab === "calculator"
                ? "text-blue-400 border-blue-400"
                : "text-gray-400 border-transparent hover:text-gray-200"
            }`}
          >
            Calculator
          </button>
          <button
            onClick={() => setActiveTab("deduction")}
            className={`px-6 py-3 text-sm font-medium transition border-b-2 ${
              activeTab === "deduction"
                ? "text-blue-400 border-blue-400"
                : "text-gray-400 border-transparent hover:text-gray-200"
            }`}
          >
            Deduction
          </button>
        </div>

        {/* Calculator Tab */}
        {activeTab === "calculator" && (
          <div className="space-y-6">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-100">
                Calculate Self-Employment Tax
              </h2>
              <p className="text-sm text-gray-400 mb-6">
                Calculate your self-employment tax (Schedule SE) based on net profit from
                Schedule C or F. Uses 2025 tax rates: 12.4% Social Security (up to $168,600),
                2.9% Medicare (all earnings), and 0.9% Additional Medicare (above $200k/$250k).
              </p>

              <form onSubmit={handleCalculate} className="space-y-4">
                {/* Net Self-Employment Income */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Net Self-Employment Income (USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={calculatorForm.net_self_employment_income}
                    onChange={(e) =>
                      setCalculatorForm({ ...calculatorForm, net_self_employment_income: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="75000.00"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Net profit from Schedule C (self-employment) or Schedule F (farm income)
                  </p>
                </div>

                {/* Filing Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Filing Status
                  </label>
                  <select
                    value={calculatorForm.filing_status}
                    onChange={(e) =>
                      setCalculatorForm({
                        ...calculatorForm,
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
                    Affects Additional Medicare threshold ($200k single, $250k married jointly)
                  </p>
                </div>

                {/* Tax Year */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Tax Year
                  </label>
                  <input
                    type="number"
                    value={calculatorForm.tax_year}
                    onChange={(e) =>
                      setCalculatorForm({ ...calculatorForm, tax_year: parseInt(e.target.value) || 2025 })
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
                  disabled={calculatorLoading}
                  className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {calculatorLoading ? "Calculating..." : "Calculate SE Tax"}
                </button>
              </form>

              {/* Error */}
              {calculatorError && (
                <div className="mt-4 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
                  {calculatorError}
                </div>
              )}

              {/* Results */}
              {calculatorResult && (
                <div className="mt-6 p-6 bg-gray-800 border border-gray-700 rounded-lg space-y-3">
                  <h3 className="text-lg font-semibold text-green-400 mb-4">
                    Self-Employment Tax Breakdown
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="text-gray-400">Net SE Income:</div>
                    <div className="text-right font-mono text-gray-100">
                      {usd(calculatorResult.net_self_employment_income)}
                    </div>

                    <div className="text-gray-400">Net Earnings (92.35%):</div>
                    <div className="text-right font-mono text-gray-100">
                      {usd(calculatorResult.net_earnings_subject_to_se_tax)}
                    </div>

                    <div className="col-span-2 border-t border-gray-700 pt-2 mt-2"></div>

                    <div className="text-gray-400">Social Security Tax (12.4%):</div>
                    <div className="text-right font-mono text-gray-100">
                      {usd(calculatorResult.social_security_tax)}
                    </div>

                    <div className="text-gray-400">Medicare Tax (2.9%):</div>
                    <div className="text-right font-mono text-gray-100">
                      {usd(calculatorResult.medicare_tax)}
                    </div>

                    <div className="text-gray-400">Additional Medicare (0.9%):</div>
                    <div className="text-right font-mono text-gray-100">
                      {usd(calculatorResult.additional_medicare_tax)}
                    </div>

                    <div className="col-span-2 border-t border-gray-700 pt-2 mt-2"></div>

                    <div className="text-lg font-semibold text-gray-200">Total SE Tax:</div>
                    <div className="text-right font-mono text-lg font-bold text-green-400">
                      {usd(calculatorResult.total_self_employment_tax)}
                    </div>

                    <div className="text-gray-400">Deductible (50%):</div>
                    <div className="text-right font-mono text-blue-400">
                      {usd(calculatorResult.deductible_se_tax)}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-4 border-t border-gray-700 pt-3">
                    <strong>Note:</strong> The deductible amount ({usd(calculatorResult.deductible_se_tax)})
                    reduces your adjusted gross income (AGI) on Form 1040 Schedule 1, Line 15.
                  </p>
                </div>
              )}
            </div>

            {/* Info Box */}
            <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-300 mb-2">
                📘 About Schedule SE
              </h3>
              <ul className="text-xs text-gray-300 space-y-1">
                <li>• Self-employed individuals pay both employer and employee portions of FICA taxes</li>
                <li>• Social Security: 12.4% on earnings up to $168,600 (2025)</li>
                <li>• Medicare: 2.9% on all net earnings</li>
                <li>• Additional Medicare: 0.9% on earnings above $200k (single) or $250k (married jointly)</li>
                <li>• Deductible portion: 50% of total SE tax (IRC §164(f))</li>
                <li>• Net earnings: 92.35% of net self-employment income (IRC §1401(b))</li>
              </ul>
            </div>
          </div>
        )}

        {/* Deduction Tab */}
        {activeTab === "deduction" && (
          <div className="space-y-6">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-100">
                Calculate SE Tax Deduction
              </h2>
              <p className="text-sm text-gray-400 mb-6">
                Calculate the deductible portion of your self-employment tax (IRC §164(f)).
                This is exactly 50% of your total SE tax and reduces your AGI on Form 1040.
              </p>

              <form onSubmit={handleDeduction} className="space-y-4">
                {/* Total SE Tax */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Total Self-Employment Tax (USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={deductionForm.total_self_employment_tax}
                    onChange={(e) =>
                      setDeductionForm({ total_self_employment_tax: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="10597.50"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    From Schedule SE, Line 12 (total self-employment tax)
                  </p>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={deductionLoading}
                  className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deductionLoading ? "Calculating..." : "Calculate Deduction"}
                </button>
              </form>

              {/* Error */}
              {deductionError && (
                <div className="mt-4 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
                  {deductionError}
                </div>
              )}

              {/* Results */}
              {deductionResult && (
                <div className="mt-6 p-6 bg-gray-800 border border-gray-700 rounded-lg space-y-3">
                  <h3 className="text-lg font-semibold text-green-400 mb-4">
                    Deduction Calculation
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="text-gray-400">Total SE Tax:</div>
                    <div className="text-right font-mono text-gray-100">
                      {usd(deductionResult.total_self_employment_tax)}
                    </div>

                    <div className="col-span-2 border-t border-gray-700 pt-2 mt-2"></div>

                    <div className="text-lg font-semibold text-gray-200">Deductible Amount (50%):</div>
                    <div className="text-right font-mono text-lg font-bold text-green-400">
                      {usd(deductionResult.deductible_se_tax)}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-4 border-t border-gray-700 pt-3">
                    <strong>{deductionResult.description}</strong> — Report this amount on Form 1040
                    Schedule 1, Line 15 to reduce your adjusted gross income.
                  </p>
                </div>
              )}
            </div>

            {/* Info Box */}
            <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-300 mb-2">
                💡 About the Deduction
              </h3>
              <ul className="text-xs text-gray-300 space-y-1">
                <li>• Self-employed individuals can deduct 50% of their SE tax from gross income</li>
                <li>• This deduction approximates the employer portion of FICA taxes</li>
                <li>• Reduces adjusted gross income (AGI), not taxable income directly</li>
                <li>• Reported on Form 1040 Schedule 1, Line 15</li>
                <li>• IRC §164(f) authorizes this deduction</li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
