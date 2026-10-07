"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

// -----------------------------------------------------------------------
// Type Definitions (inline until we add to lib/api.ts)
// -----------------------------------------------------------------------

interface TenantOut {
  email: string;
  tenant_id: string;
  tenant_name: string;
}

interface FilingRequirementResult {
  eligible: boolean;
  disaster_type: string;
  distribution_within_window: boolean;
  economic_loss_threshold_met: boolean;
  max_distribution_limit: string;
  explanation: string;
}

interface RepaymentScheduleResult {
  total_distribution: string;
  annual_repayment: string;
  repayment_schedule: Array<{
    year: number;
    repayment_due: string;
    tax_if_not_repaid: string;
  }>;
  tax_spread_per_year: string;
  explanation: string;
}

interface PenaltyWaiverResult {
  waiver_eligible: boolean;
  standard_penalty_rate: string;
  waived_penalty_amount: string;
  explanation: string;
}

interface Form8915Overview {
  form: string;
  title: string;
  purpose: string;
  qualified_disaster_types: string[];
  max_distribution_limit: string;
  repayment_period_years: number;
  tax_spread: {
    period_years: number;
    annual_inclusion: string;
  };
  penalty_waiver: {
    standard_penalty_rate: string;
    waiver_applies: boolean;
    age_requirement: string;
  };
  key_requirements: string[];
  benefits: string[];
  filing_deadline: string;
  statutory_references: string[];
  irs_reference: string;
}

// -----------------------------------------------------------------------
// API Functions (inline)
// -----------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiMe(): Promise<TenantOut> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Unauthorized");
  return res.json();
}

async function apiForm8915FilingRequirement(payload: {
  disaster_area: string;
  distribution_date: string;
  home_destroyed: boolean;
  economic_loss_amt: string;
}): Promise<FilingRequirementResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/form8915/filing-requirement`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("API request failed");
  return res.json();
}

async function apiForm8915RepaymentSchedule(payload: {
  distribution_amt: string;
  repayment_years: number;
}): Promise<RepaymentScheduleResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/form8915/repayment-schedule`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("API request failed");
  return res.json();
}

async function apiForm8915PenaltyWaiver(payload: {
  age: number;
  distribution_amt: string;
}): Promise<PenaltyWaiverResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/form8915/penalty-waiver`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("API request failed");
  return res.json();
}

async function apiForm8915Overview(): Promise<Form8915Overview> {
  const res = await fetch(`${API_BASE}/api/v1/form8915/overview`);
  if (!res.ok) throw new Error("Failed to load overview");
  return res.json();
}

// -----------------------------------------------------------------------
// Main Page Component
// -----------------------------------------------------------------------

export default function Form8915Page() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [authError, setAuthError] = useState(false);
  const [activeTab, setActiveTab] = useState<"filing" | "repayment" | "overview">("filing");

  // Filing Requirement form state
  const [disasterArea, setDisasterArea] = useState("Hurricane Ian, Florida");
  const [distributionDate, setDistributionDate] = useState("2024-09-28");
  const [homeDestroyed, setHomeDestroyed] = useState(true);
  const [economicLoss, setEconomicLoss] = useState("0");

  // Repayment Schedule form state
  const [distributionAmt, setDistributionAmt] = useState("75000");
  const [repaymentYears, setRepaymentYears] = useState(3);

  // Penalty Waiver (combined with Filing Requirement)
  const [age, setAge] = useState(45);

  // Results
  const [filingResult, setFilingResult] = useState<FilingRequirementResult | null>(null);
  const [repaymentResult, setRepaymentResult] = useState<RepaymentScheduleResult | null>(null);
  const [penaltyResult, setPenaltyResult] = useState<PenaltyWaiverResult | null>(null);
  const [overview, setOverview] = useState<Form8915Overview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---- Auth guard ----
  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }
    apiMe()
      .then(setTenant)
      .catch(() => {
        localStorage.removeItem("jwt_token");
        setAuthError(true);
        router.replace("/auth/login");
      });
  }, [router]);

  // ---- Load overview on mount ----
  useEffect(() => {
    apiForm8915Overview()
      .then(setOverview)
      .catch(() => {
        // Overview is non-critical
      });
  }, []);

  // ---- Filing Requirement submission ----
  async function handleFilingSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setFilingResult(null);
    setPenaltyResult(null);
    setLoading(true);

    try {
      const result = await apiForm8915FilingRequirement({
        disaster_area: disasterArea,
        distribution_date: distributionDate,
        home_destroyed: homeDestroyed,
        economic_loss_amt: economicLoss,
      });
      setFilingResult(result);

      // Also fetch penalty waiver if eligible
      if (result.eligible && distributionAmt) {
        const penaltyRes = await apiForm8915PenaltyWaiver({
          age: age,
          distribution_amt: distributionAmt,
        });
        setPenaltyResult(penaltyRes);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  // ---- Repayment Schedule submission ----
  async function handleRepaymentSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setRepaymentResult(null);
    setLoading(true);

    try {
      const result = await apiForm8915RepaymentSchedule({
        distribution_amt: distributionAmt,
        repayment_years: repaymentYears,
      });
      setRepaymentResult(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  if (authError) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="no-print bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <span className="font-extrabold text-brand-800 text-lg">
          🇺🇸 US Expat Tax
        </span>
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">
            Dashboard
          </Link>
          {tenant && (
            <span className="text-xs text-gray-500">
              {tenant.tenant_name} ({tenant.email})
            </span>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold mb-2 text-gray-800">
            Form 8915 — Qualified Disaster Retirement Plan Distributions
          </h1>
          <p className="text-gray-600 mb-6">
            Calculate eligibility, repayment schedules, and penalty waivers for
            qualified disaster distributions from retirement plans.
          </p>

          {/* Tabs */}
          <div className="border-b border-gray-200 mb-6">
            <div className="flex space-x-8">
              <button
                onClick={() => setActiveTab("filing")}
                className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "filing"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                Filing Requirement
              </button>
              <button
                onClick={() => setActiveTab("repayment")}
                className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "repayment"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                Repayment Schedule
              </button>
              <button
                onClick={() => setActiveTab("overview")}
                className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "overview"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                Overview
              </button>
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === "filing" && (
            <div>
              <h2 className="text-xl font-semibold mb-4 text-gray-800">
                Check Eligibility for Qualified Disaster Distribution
              </h2>
              <form onSubmit={handleFilingSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Disaster Area
                  </label>
                  <input
                    type="text"
                    value={disasterArea}
                    onChange={(e) => setDisasterArea(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="e.g., Hurricane Ian, Florida"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Distribution Date (YYYY-MM-DD)
                  </label>
                  <input
                    type="date"
                    value={distributionDate}
                    onChange={(e) => setDistributionDate(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={homeDestroyed}
                    onChange={(e) => setHomeDestroyed(e.target.checked)}
                    id="homeDestroyed"
                    className="w-4 h-4"
                  />
                  <label htmlFor="homeDestroyed" className="text-sm text-gray-700">
                    Principal residence was destroyed
                  </label>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Economic Loss (USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={economicLoss}
                    onChange={(e) => setEconomicLoss(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Distribution Amount (USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={distributionAmt}
                    onChange={(e) => setDistributionAmt(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="75000.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Your Age
                  </label>
                  <input
                    type="number"
                    value={age}
                    onChange={(e) => setAge(parseInt(e.target.value, 10))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="45"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded disabled:opacity-50"
                >
                  {loading ? "Checking..." : "Check Eligibility"}
                </button>
              </form>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
                  {error}
                </div>
              )}

              {filingResult && (
                <div className={`mt-6 p-6 rounded border ${
                  filingResult.eligible
                    ? "bg-green-50 border-green-200"
                    : "bg-yellow-50 border-yellow-200"
                }`}>
                  <h3 className="text-lg font-semibold mb-2">
                    {filingResult.eligible ? "✅ ELIGIBLE" : "⚠️ NOT ELIGIBLE"}
                  </h3>
                  <p className="text-sm mb-3">{filingResult.explanation}</p>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <strong>Disaster Type:</strong> {filingResult.disaster_type}
                    </div>
                    <div>
                      <strong>Max Distribution:</strong> ${filingResult.max_distribution_limit}
                    </div>
                    <div>
                      <strong>Within Window:</strong>{" "}
                      {filingResult.distribution_within_window ? "Yes" : "No"}
                    </div>
                    <div>
                      <strong>Economic Loss Met:</strong>{" "}
                      {filingResult.economic_loss_threshold_met ? "Yes" : "No"}
                    </div>
                  </div>
                </div>
              )}

              {penaltyResult && (
                <div className="mt-4 p-6 rounded border bg-blue-50 border-blue-200">
                  <h3 className="text-lg font-semibold mb-2">
                    💰 Penalty Waiver
                  </h3>
                  <p className="text-sm mb-3">{penaltyResult.explanation}</p>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <strong>Waiver Eligible:</strong>{" "}
                      {penaltyResult.waiver_eligible ? "Yes" : "No"}
                    </div>
                    <div>
                      <strong>Penalty Saved:</strong> ${penaltyResult.waived_penalty_amount}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "repayment" && (
            <div>
              <h2 className="text-xl font-semibold mb-4 text-gray-800">
                Calculate Repayment Schedule
              </h2>
              <form onSubmit={handleRepaymentSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Distribution Amount (USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={distributionAmt}
                    onChange={(e) => setDistributionAmt(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    placeholder="75000.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Repayment Period (years, max 3)
                  </label>
                  <select
                    value={repaymentYears}
                    onChange={(e) => setRepaymentYears(parseInt(e.target.value, 10))}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  >
                    <option value="1">1 year</option>
                    <option value="2">2 years</option>
                    <option value="3">3 years</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded disabled:opacity-50"
                >
                  {loading ? "Calculating..." : "Calculate Schedule"}
                </button>
              </form>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
                  {error}
                </div>
              )}

              {repaymentResult && (
                <div className="mt-6 p-6 rounded border bg-green-50 border-green-200">
                  <h3 className="text-lg font-semibold mb-2">
                    📅 Repayment Schedule
                  </h3>
                  <p className="text-sm mb-4">{repaymentResult.explanation}</p>

                  <div className="mb-4 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <strong>Total Distribution:</strong> ${repaymentResult.total_distribution}
                    </div>
                    <div>
                      <strong>Annual Repayment:</strong> ${repaymentResult.annual_repayment}
                    </div>
                    <div>
                      <strong>Tax Spread/Year (if NOT repaid):</strong> ${repaymentResult.tax_spread_per_year}
                    </div>
                  </div>

                  <table className="w-full text-sm border border-gray-300">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="border border-gray-300 px-3 py-2 text-left">Year</th>
                        <th className="border border-gray-300 px-3 py-2 text-left">
                          Repayment Due
                        </th>
                        <th className="border border-gray-300 px-3 py-2 text-left">
                          Tax if NOT Repaid
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {repaymentResult.repayment_schedule.map((item, idx) => (
                        <tr key={idx}>
                          <td className="border border-gray-300 px-3 py-2">{item.year}</td>
                          <td className="border border-gray-300 px-3 py-2">
                            ${item.repayment_due}
                          </td>
                          <td className="border border-gray-300 px-3 py-2">
                            ${item.tax_if_not_repaid}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === "overview" && overview && (
            <div>
              <h2 className="text-xl font-semibold mb-4 text-gray-800">
                {overview.title}
              </h2>
              <p className="text-sm text-gray-700 mb-4">{overview.purpose}</p>

              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Qualified Disaster Types
                  </h3>
                  <ul className="list-disc list-inside text-sm text-gray-700">
                    {overview.qualified_disaster_types.map((t, i) => (
                      <li key={i}>{t}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Key Requirements
                  </h3>
                  <ul className="list-disc list-inside text-sm text-gray-700">
                    {overview.key_requirements.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Benefits
                  </h3>
                  <ul className="list-disc list-inside text-sm text-gray-700">
                    {overview.benefits.map((b, i) => (
                      <li key={i}>{b}</li>
                    ))}
                  </ul>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <strong>Max Distribution:</strong> ${overview.max_distribution_limit}
                  </div>
                  <div>
                    <strong>Repayment Period:</strong> {overview.repayment_period_years} years
                  </div>
                  <div>
                    <strong>Filing Deadline:</strong> {overview.filing_deadline}
                  </div>
                  <div>
                    <strong>Penalty Waiver:</strong>{" "}
                    {overview.penalty_waiver.waiver_applies ? "Yes" : "No"}
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Statutory References
                  </h3>
                  <ul className="list-disc list-inside text-sm text-gray-700">
                    {overview.statutory_references.map((ref, i) => (
                      <li key={i}>{ref}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <a
                    href={overview.irs_reference}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline text-sm"
                  >
                    📄 IRS Form 8915 Reference
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
