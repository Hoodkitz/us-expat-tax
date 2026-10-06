"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FilingRequirementRequest {
  has_pfic_interest: boolean;
  had_sale_or_distribution: boolean;
  received_excess_distribution: boolean;
}

interface FilingRequirementResult {
  filing_required: boolean;
  reasons: string[];
  penalty_if_not_filed: number;
  recommendation: string;
}

interface MTMCalculationRequest {
  beginning_fmv: number;
  ending_fmv: number;
  tax_year: number;
}

interface MTMCalculationResult {
  unrealized_gain_or_loss: number;
  ordinary_income_or_loss: number;
  beginning_fmv: number;
  ending_fmv: number;
  tax_treatment: string;
  explanation: string;
}

interface QEFCalculationRequest {
  ordinary_earnings: number;
  net_capital_gain: number;
  ownership_percentage: number;
  tax_year: number;
}

interface QEFCalculationResult {
  ordinary_earnings_includible: number;
  capital_gain_includible: number;
  total_inclusion: number;
  ownership_percentage: number;
  explanation: string;
}

interface ExcessDistributionRequest {
  total_distribution: number;
  holding_period_years: number;
  prior_distributions: number[];
  tax_year: number;
}

interface ExcessDistributionResult {
  total_distribution: number;
  average_distribution: number;
  excess_amount: number;
  deferred_tax_amount: number;
  interest_charge: number;
  total_tax_and_interest: number;
  allocation_by_year: Array<{
    year: number;
    allocated_amount: number;
    tax_on_allocation: number;
  }>;
  explanation: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function fmtUSD(val: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(val);
}

// ---------------------------------------------------------------------------
// Filing Check Tab
// ---------------------------------------------------------------------------

function FilingCheckTab() {
  const [form, setForm] = useState<FilingRequirementRequest>({
    has_pfic_interest: false,
    had_sale_or_distribution: false,
    received_excess_distribution: false,
  });
  const [result, setResult] = useState<FilingRequirementResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/form8621/filing-requirement`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        }
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Form 8621 Filing Check</h2>
        <p className="text-sm text-gray-600 mb-4">
          Determine if you are required to file Form 8621 for Passive Foreign
          Investment Companies (PFICs).
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={form.has_pfic_interest}
                onChange={(e) =>
                  setForm({ ...form, has_pfic_interest: e.target.checked })
                }
                className="h-4 w-4"
              />
              <span className="text-sm">
                I hold a direct or indirect interest in a PFIC (e.g., foreign
                mutual fund, foreign ETF)
              </span>
            </label>
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={form.had_sale_or_distribution}
                onChange={(e) =>
                  setForm({
                    ...form,
                    had_sale_or_distribution: e.target.checked,
                  })
                }
                className="h-4 w-4"
              />
              <span className="text-sm">
                I sold PFIC shares or received a distribution this year
              </span>
            </label>
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={form.received_excess_distribution}
                onChange={(e) =>
                  setForm({
                    ...form,
                    received_excess_distribution: e.target.checked,
                  })
                }
                className="h-4 w-4"
              />
              <span className="text-sm">
                I received an excess distribution (distribution exceeding 125%
                of average)
              </span>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? "Checking..." : "Check Filing Requirement"}
          </button>
        </form>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded p-4">
            <p className="text-sm text-red-800">Error: {error}</p>
          </div>
        )}

        {result && (
          <div className="mt-6 space-y-4">
            <div
              className={`p-4 rounded ${
                result.filing_required
                  ? "bg-yellow-50 border border-yellow-200"
                  : "bg-green-50 border border-green-200"
              }`}
            >
              <h3 className="font-bold text-lg mb-2">
                {result.filing_required
                  ? "⚠️ Filing Required"
                  : "✓ Filing Not Required"}
              </h3>
              <ul className="list-disc list-inside space-y-1">
                {result.reasons.map((reason, idx) => (
                  <li key={idx} className="text-sm">
                    {reason}
                  </li>
                ))}
              </ul>
              {result.penalty_if_not_filed > 0 && (
                <p className="mt-2 text-sm font-semibold text-red-700">
                  Penalty for non-filing: {fmtUSD(result.penalty_if_not_filed)}
                </p>
              )}
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded p-4">
              <p className="text-sm">{result.recommendation}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Elections Tab (MTM & QEF)
// ---------------------------------------------------------------------------

function ElectionsTab() {
  const [activeElection, setActiveElection] = useState<"mtm" | "qef">("mtm");

  // MTM state
  const [mtmForm, setMtmForm] = useState<MTMCalculationRequest>({
    beginning_fmv: 100000,
    ending_fmv: 115000,
    tax_year: 2024,
  });
  const [mtmResult, setMtmResult] = useState<MTMCalculationResult | null>(
    null
  );
  const [mtmLoading, setMtmLoading] = useState(false);
  const [mtmError, setMtmError] = useState<string | null>(null);

  // QEF state
  const [qefForm, setQefForm] = useState<QEFCalculationRequest>({
    ordinary_earnings: 5000,
    net_capital_gain: 2000,
    ownership_percentage: 10,
    tax_year: 2024,
  });
  const [qefResult, setQefResult] = useState<QEFCalculationResult | null>(
    null
  );
  const [qefLoading, setQefLoading] = useState(false);
  const [qefError, setQefError] = useState<string | null>(null);

  const handleMtmSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMtmLoading(true);
    setMtmError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/form8621/mtm-calculation`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(mtmForm),
        }
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setMtmResult(data);
    } catch (err: any) {
      setMtmError(err.message || "Request failed");
    } finally {
      setMtmLoading(false);
    }
  };

  const handleQefSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setQefLoading(true);
    setQefError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/form8621/qef-calculation`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(qefForm),
        }
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setQefResult(data);
    } catch (err: any) {
      setQefError(err.message || "Request failed");
    } finally {
      setQefLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">PFIC Elections</h2>
        <div className="flex space-x-4 mb-6">
          <button
            onClick={() => setActiveElection("mtm")}
            className={`px-4 py-2 rounded ${
              activeElection === "mtm"
                ? "bg-blue-600 text-white"
                : "bg-gray-200"
            }`}
          >
            Mark-to-Market (§1296)
          </button>
          <button
            onClick={() => setActiveElection("qef")}
            className={`px-4 py-2 rounded ${
              activeElection === "qef"
                ? "bg-blue-600 text-white"
                : "bg-gray-200"
            }`}
          >
            QEF Election (§1293)
          </button>
        </div>

        {activeElection === "mtm" ? (
          <div>
            <p className="text-sm text-gray-600 mb-4">
              Mark-to-Market election: Recognize annual unrealized gains/losses
              as ordinary income/loss.
            </p>
            <form onSubmit={handleMtmSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Beginning FMV (Fair Market Value)
                </label>
                <input
                  type="number"
                  value={mtmForm.beginning_fmv}
                  onChange={(e) =>
                    setMtmForm({
                      ...mtmForm,
                      beginning_fmv: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Ending FMV (Fair Market Value)
                </label>
                <input
                  type="number"
                  value={mtmForm.ending_fmv}
                  onChange={(e) =>
                    setMtmForm({
                      ...mtmForm,
                      ending_fmv: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Tax Year
                </label>
                <input
                  type="number"
                  value={mtmForm.tax_year}
                  onChange={(e) =>
                    setMtmForm({
                      ...mtmForm,
                      tax_year: parseInt(e.target.value) || 2024,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <button
                type="submit"
                disabled={mtmLoading}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {mtmLoading ? "Calculating..." : "Calculate MTM"}
              </button>
            </form>

            {mtmError && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded p-4">
                <p className="text-sm text-red-800">Error: {mtmError}</p>
              </div>
            )}

            {mtmResult && (
              <div className="mt-6 space-y-4">
                <div className="bg-gray-50 border rounded p-4">
                  <h3 className="font-bold mb-2">MTM Calculation Result</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Beginning FMV:</span>
                      <span className="font-semibold">
                        {fmtUSD(mtmResult.beginning_fmv)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Ending FMV:</span>
                      <span className="font-semibold">
                        {fmtUSD(mtmResult.ending_fmv)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Unrealized Gain/Loss:</span>
                      <span
                        className={`font-semibold ${
                          mtmResult.unrealized_gain_or_loss >= 0
                            ? "text-green-700"
                            : "text-red-700"
                        }`}
                      >
                        {fmtUSD(mtmResult.unrealized_gain_or_loss)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tax Treatment:</span>
                      <span className="font-semibold">
                        {mtmResult.tax_treatment}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded p-4">
                  <p className="text-sm">{mtmResult.explanation}</p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div>
            <p className="text-sm text-gray-600 mb-4">
              QEF election: Include pro-rata share of PFIC&apos;s ordinary earnings
              and net capital gain annually.
            </p>
            <form onSubmit={handleQefSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Ordinary Earnings (from PFIC statement)
                </label>
                <input
                  type="number"
                  value={qefForm.ordinary_earnings}
                  onChange={(e) =>
                    setQefForm({
                      ...qefForm,
                      ordinary_earnings: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Net Capital Gain (from PFIC statement)
                </label>
                <input
                  type="number"
                  value={qefForm.net_capital_gain}
                  onChange={(e) =>
                    setQefForm({
                      ...qefForm,
                      net_capital_gain: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Ownership Percentage (%)
                </label>
                <input
                  type="number"
                  value={qefForm.ownership_percentage}
                  onChange={(e) =>
                    setQefForm({
                      ...qefForm,
                      ownership_percentage: parseFloat(e.target.value) || 0,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                  step="0.01"
                  max="100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Tax Year
                </label>
                <input
                  type="number"
                  value={qefForm.tax_year}
                  onChange={(e) =>
                    setQefForm({
                      ...qefForm,
                      tax_year: parseInt(e.target.value) || 2024,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <button
                type="submit"
                disabled={qefLoading}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {qefLoading ? "Calculating..." : "Calculate QEF"}
              </button>
            </form>

            {qefError && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded p-4">
                <p className="text-sm text-red-800">Error: {qefError}</p>
              </div>
            )}

            {qefResult && (
              <div className="mt-6 space-y-4">
                <div className="bg-gray-50 border rounded p-4">
                  <h3 className="font-bold mb-2">QEF Calculation Result</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Ownership Percentage:</span>
                      <span className="font-semibold">
                        {qefResult.ownership_percentage}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Ordinary Earnings (Includible):</span>
                      <span className="font-semibold">
                        {fmtUSD(qefResult.ordinary_earnings_includible)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Capital Gain (Includible):</span>
                      <span className="font-semibold">
                        {fmtUSD(qefResult.capital_gain_includible)}
                      </span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span className="font-bold">Total Inclusion:</span>
                      <span className="font-bold text-blue-700">
                        {fmtUSD(qefResult.total_inclusion)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded p-4">
                  <p className="text-sm">{qefResult.explanation}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Excess Distribution Tab
// ---------------------------------------------------------------------------

function ExcessDistributionTab() {
  const [form, setForm] = useState<ExcessDistributionRequest>({
    total_distribution: 20000,
    holding_period_years: 5,
    prior_distributions: [8000, 7500, 9000],
    tax_year: 2024,
  });
  const [result, setResult] = useState<ExcessDistributionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [priorDistInput, setPriorDistInput] = useState<string>("8000, 7500, 9000");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Parse prior distributions
    const priorDist = priorDistInput
      .split(",")
      .map((s) => parseFloat(s.trim()))
      .filter((n) => !isNaN(n));

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/form8621/excess-distribution`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...form,
            prior_distributions: priorDist,
          }),
        }
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">
          Excess Distribution Calculator
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Calculate deferred tax and interest charge under the default regime
          (§1291). Applies when no QEF or MTM election is made.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Total Distribution Received
            </label>
            <input
              type="number"
              value={form.total_distribution}
              onChange={(e) =>
                setForm({
                  ...form,
                  total_distribution: parseFloat(e.target.value) || 0,
                })
              }
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Holding Period (Years)
            </label>
            <input
              type="number"
              value={form.holding_period_years}
              onChange={(e) =>
                setForm({
                  ...form,
                  holding_period_years: parseInt(e.target.value) || 1,
                })
              }
              className="w-full border rounded px-3 py-2"
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Prior Distributions (comma-separated, last 3 years)
            </label>
            <input
              type="text"
              value={priorDistInput}
              onChange={(e) => setPriorDistInput(e.target.value)}
              placeholder="8000, 7500, 9000"
              className="w-full border rounded px-3 py-2"
            />
            <p className="text-xs text-gray-500 mt-1">
              Example: 8000, 7500, 9000 (leave empty if no prior distributions)
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Tax Year</label>
            <input
              type="number"
              value={form.tax_year}
              onChange={(e) =>
                setForm({
                  ...form,
                  tax_year: parseInt(e.target.value) || 2024,
                })
              }
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? "Calculating..." : "Calculate Excess Distribution"}
          </button>
        </form>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded p-4">
            <p className="text-sm text-red-800">Error: {error}</p>
          </div>
        )}

        {result && (
          <div className="mt-6 space-y-4">
            <div className="bg-gray-50 border rounded p-4">
              <h3 className="font-bold mb-2">Excess Distribution Result</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Total Distribution:</span>
                  <span className="font-semibold">
                    {fmtUSD(result.total_distribution)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Average Prior Distribution:</span>
                  <span className="font-semibold">
                    {fmtUSD(result.average_distribution)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Excess Amount:</span>
                  <span
                    className={`font-semibold ${
                      result.excess_amount > 0 ? "text-red-700" : "text-green-700"
                    }`}
                  >
                    {fmtUSD(result.excess_amount)}
                  </span>
                </div>
                {result.excess_amount > 0 && (
                  <>
                    <div className="flex justify-between">
                      <span>Deferred Tax Amount:</span>
                      <span className="font-semibold">
                        {fmtUSD(result.deferred_tax_amount)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Interest Charge (§1291):</span>
                      <span className="font-semibold">
                        {fmtUSD(result.interest_charge)}
                      </span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span className="font-bold">Total Tax + Interest:</span>
                      <span className="font-bold text-red-700">
                        {fmtUSD(result.total_tax_and_interest)}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {result.allocation_by_year.length > 0 && result.excess_amount > 0 && (
              <div className="bg-gray-50 border rounded p-4">
                <h3 className="font-bold mb-2">Allocation by Year</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2">Year</th>
                        <th className="text-right py-2">Allocated Amount</th>
                        <th className="text-right py-2">Tax on Allocation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.allocation_by_year.map((row, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="py-2">{row.year}</td>
                          <td className="text-right">
                            {fmtUSD(row.allocated_amount)}
                          </td>
                          <td className="text-right">
                            {fmtUSD(row.tax_on_allocation)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded p-4">
              <p className="text-sm">{result.explanation}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function Form8621Page() {
  const [activeTab, setActiveTab] = useState<
    "filing" | "elections" | "excess"
  >("filing");

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-6">
          <Link
            href="/dashboard"
            className="text-blue-600 hover:underline text-sm"
          >
            ← Back to Dashboard
          </Link>
        </div>

        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h1 className="text-3xl font-bold mb-2">
            Form 8621: PFIC Reporting
          </h1>
          <p className="text-gray-600">
            Passive Foreign Investment Company (PFIC) reporting for US expats
            holding foreign mutual funds, ETFs, or pooled investments.
          </p>
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded p-4">
            <p className="text-sm text-yellow-800">
              <strong>⚠️ Warning:</strong> PFIC reporting is complex. Consult a
              tax professional before filing. Penalties for non-filing: $10,000
              per year.
            </p>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex space-x-4">
            <button
              onClick={() => setActiveTab("filing")}
              className={`px-6 py-3 rounded-t-lg font-medium ${
                activeTab === "filing"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-700"
              }`}
            >
              Filing Check
            </button>
            <button
              onClick={() => setActiveTab("elections")}
              className={`px-6 py-3 rounded-t-lg font-medium ${
                activeTab === "elections"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-700"
              }`}
            >
              Elections (MTM/QEF)
            </button>
            <button
              onClick={() => setActiveTab("excess")}
              className={`px-6 py-3 rounded-t-lg font-medium ${
                activeTab === "excess"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-700"
              }`}
            >
              Excess Distribution
            </button>
          </div>
        </div>

        {activeTab === "filing" && <FilingCheckTab />}
        {activeTab === "elections" && <ElectionsTab />}
        {activeTab === "excess" && <ExcessDistributionTab />}
      </div>
    </div>
  );
}
