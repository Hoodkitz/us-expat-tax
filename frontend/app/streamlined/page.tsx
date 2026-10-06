"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiMe } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EligibilityRequest {
  days_in_us_per_year: number[];
  had_filing_requirement: boolean;
  filed_returns: boolean;
  filed_fbars: boolean;
  is_willful: boolean;
  account_balance_usd: number;
  years_unreported: number;
}

interface EligibilityResult {
  qualifies_sfop: boolean;
  qualifies_sdop: boolean;
  procedure: "SFOP" | "SDOP" | "none";
  penalty_rate: number;
  estimated_penalty_usd: number;
  required_returns: number;
  required_fbars: number;
  non_willful_certification_required: boolean;
  steps: string[];
  revenue_procedure: string;
  warnings: string[];
}

interface PenaltyResult {
  highest_aggregate_balance: number;
  penalty_rate: number;
  penalty_amount: number;
  years_analyzed: string[];
  explanation: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function apiStreamlinedEligibility(payload: EligibilityRequest): Promise<EligibilityResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/streamlined/eligibility`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

async function apiStreamlinedPenalty(
  balancesByYear: Record<string, number>,
  years: string[]
): Promise<PenaltyResult> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/v1/streamlined/penalty-calculation`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ account_balances_by_year: balancesByYear, years }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Helper to format USD
// ---------------------------------------------------------------------------
function usd(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(n);
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tab = "eligibility" | "penalty";

export default function StreamlinedPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("eligibility");

  // Eligibility form state
  const [daysYear1, setDaysYear1] = useState("20");
  const [daysYear2, setDaysYear2] = useState("25");
  const [daysYear3, setDaysYear3] = useState("30");
  const [hadFilingReq, setHadFilingReq] = useState(true);
  const [filedReturns, setFiledReturns] = useState(false);
  const [filedFbars, setFiledFbars] = useState(false);
  const [isWillful, setIsWillful] = useState(false);
  const [accountBalance, setAccountBalance] = useState("100000");
  const [yearsUnreported, setYearsUnreported] = useState("3");

  // Penalty calculator state
  const [penaltyYears, setPenaltyYears] = useState<string[]>(["2021", "2022", "2023"]);
  const [penaltyBalances, setPenaltyBalances] = useState<Record<string, string>>({
    "2021": "100000",
    "2022": "150000",
    "2023": "130000",
  });

  // Results
  const [eligibilityResult, setEligibilityResult] = useState<EligibilityResult | null>(null);
  const [penaltyResult, setPenaltyResult] = useState<PenaltyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auth guard
  useEffect(() => {
    apiMe()
      .then(() => setAuthReady(true))
      .catch(() => router.push("/login"));
  }, [router]);

  if (!authReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950 text-white">
        <div className="animate-pulse text-gray-400">Loading…</div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Submit handlers
  // ---------------------------------------------------------------------------
  async function handleEligibilitySubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await apiStreamlinedEligibility({
        days_in_us_per_year: [
          parseInt(daysYear1, 10) || 0,
          parseInt(daysYear2, 10) || 0,
          parseInt(daysYear3, 10) || 0,
        ],
        had_filing_requirement: hadFilingReq,
        filed_returns: filedReturns,
        filed_fbars: filedFbars,
        is_willful: isWillful,
        account_balance_usd: parseFloat(accountBalance) || 0,
        years_unreported: parseInt(yearsUnreported, 10) || 0,
      });
      setEligibilityResult(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function handlePenaltySubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const balancesNumeric: Record<string, number> = {};
      for (const yr of penaltyYears) {
        balancesNumeric[yr] = parseFloat(penaltyBalances[yr] ?? "0") || 0;
      }
      const result = await apiStreamlinedPenalty(balancesNumeric, penaltyYears);
      setPenaltyResult(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Procedure badge
  // ---------------------------------------------------------------------------
  function ProcedureBadge({ procedure }: { procedure: string }) {
    const colours: Record<string, string> = {
      SFOP: "bg-emerald-600 text-white",
      SDOP: "bg-amber-500 text-black",
      none: "bg-red-700 text-white",
    };
    const labels: Record<string, string> = {
      SFOP: "✓ SFOP — Streamlined Foreign Offshore",
      SDOP: "⚠ SDOP — Streamlined Domestic Offshore",
      none: "✗ Not Eligible",
    };
    return (
      <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${colours[procedure] ?? "bg-gray-600 text-white"}`}>
        {labels[procedure] ?? procedure}
      </span>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Nav */}
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-gray-400 hover:text-white transition-colors text-sm">
            ← Dashboard
          </Link>
          <span className="text-gray-600">|</span>
          <h1 className="text-lg font-semibold text-white">
            Streamlined Filing Compliance Procedures
          </h1>
        </div>
        <span className="text-xs text-gray-500">Rev. Proc. 2014-55</span>
      </nav>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Hero banner */}
        <div className="bg-blue-900/30 border border-blue-700/40 rounded-xl p-5">
          <p className="text-blue-300 text-sm leading-relaxed">
            <span className="font-semibold text-blue-200">IRS Streamlined Filing Procedures</span> allow US taxpayers
            to correct unintentional failures to report foreign financial assets with reduced or zero penalties.{" "}
            <span className="font-semibold">Offshore (SFOP)</span>: zero penalty.{" "}
            <span className="font-semibold">Domestic (SDOP)</span>: 5% of highest aggregate balance.
            Both require 3 years of amended returns + 6 years of FBARs.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-800 pb-0">
          {(["eligibility", "penalty"] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); setError(null); }}
              className={`px-5 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab
                  ? "bg-gray-800 text-white border border-b-transparent border-gray-700"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {tab === "eligibility" ? "Eligibility Checker" : "Penalty Calculator"}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-900/40 border border-red-700 rounded-lg p-4 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* ELIGIBILITY TAB                                                      */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === "eligibility" && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Form */}
            <form onSubmit={handleEligibilitySubmit} className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-5">
              <h2 className="text-base font-semibold text-white">Eligibility Questionnaire</h2>

              {/* Days in US */}
              <fieldset className="space-y-2">
                <legend className="text-sm text-gray-300 font-medium">
                  Days present in the US (last 3 calendar years, oldest → newest)
                </legend>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "Year −3", value: daysYear1, set: setDaysYear1 },
                    { label: "Year −2", value: daysYear2, set: setDaysYear2 },
                    { label: "Last year", value: daysYear3, set: setDaysYear3 },
                  ].map(({ label, value, set }) => (
                    <div key={label}>
                      <label className="text-xs text-gray-400 mb-1 block">{label}</label>
                      <input
                        type="number"
                        min={0}
                        max={366}
                        value={value}
                        onChange={(e) => set(e.target.value)}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                        required
                      />
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500">
                  ≤ 35 days/year in all 3 years → qualifies for SFOP (zero penalty)
                </p>
              </fieldset>

              {/* Account balance */}
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-1">
                  Highest foreign account balance (USD)
                </label>
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={accountBalance}
                  onChange={(e) => setAccountBalance(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Used to estimate SDOP 5% penalty</p>
              </div>

              {/* Years unreported */}
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-1">
                  Years with unreported accounts/income
                </label>
                <input
                  type="number"
                  min={0}
                  max={50}
                  value={yearsUnreported}
                  onChange={(e) => setYearsUnreported(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                  required
                />
              </div>

              {/* Checkboxes */}
              <fieldset className="space-y-2">
                <legend className="text-sm text-gray-300 font-medium mb-2">Filing history</legend>
                {[
                  { label: "I had a US filing requirement", checked: hadFilingReq, set: setHadFilingReq },
                  { label: "I already filed US tax returns for those years", checked: filedReturns, set: setFiledReturns },
                  { label: "I already filed FBARs (FinCEN 114) for those years", checked: filedFbars, set: setFiledFbars },
                ].map(({ label, checked, set }) => (
                  <label key={label} className="flex items-center gap-3 text-sm text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => set(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-600"
                    />
                    {label}
                  </label>
                ))}
              </fieldset>

              {/* Willfulness — highlighted */}
              <div className="bg-red-900/20 border border-red-800/40 rounded-lg p-4">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isWillful}
                    onChange={(e) => setIsWillful(e.target.checked)}
                    className="w-4 h-4 mt-0.5 rounded border-gray-600 bg-gray-800 text-red-600 focus:ring-red-600"
                  />
                  <span className="text-sm text-red-300">
                    <span className="font-semibold">My non-compliance was willful</span>
                    <br />
                    <span className="text-red-400/80 text-xs">
                      Willful non-compliance disqualifies you from both procedures.
                      Consult an attorney before proceeding.
                    </span>
                  </span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
              >
                {loading ? "Checking…" : "Check Eligibility"}
              </button>
            </form>

            {/* Results */}
            <div className="space-y-4">
              {!eligibilityResult && (
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 flex flex-col items-center justify-center h-64 text-gray-500 text-sm">
                  <svg className="w-10 h-10 mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Fill out the questionnaire to see your eligibility result
                </div>
              )}

              {eligibilityResult && (
                <>
                  {/* Procedure result card */}
                  <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-gray-200">Eligibility Result</h3>
                      <ProcedureBadge procedure={eligibilityResult.procedure} />
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <Stat label="Penalty Rate" value={`${(eligibilityResult.penalty_rate * 100).toFixed(0)}%`}
                        highlight={eligibilityResult.penalty_rate === 0 ? "green" : "amber"} />
                      <Stat label="Est. Penalty" value={usd(eligibilityResult.estimated_penalty_usd)}
                        highlight={eligibilityResult.estimated_penalty_usd === 0 ? "green" : "amber"} />
                      <Stat label="Amended Returns" value={`${eligibilityResult.required_returns} years`} />
                      <Stat label="FBAR Periods" value={`${eligibilityResult.required_fbars} years`} />
                    </div>

                    {eligibilityResult.non_willful_certification_required && (
                      <div className="bg-blue-900/20 border border-blue-800/40 rounded-lg px-3 py-2 text-xs text-blue-300">
                        Non-willful certification required:{" "}
                        <span className="font-semibold">
                          {eligibilityResult.procedure === "SFOP" ? "Form 14653" : "Form 14654"}
                        </span>
                      </div>
                    )}

                    <p className="text-xs text-gray-500">{eligibilityResult.revenue_procedure}</p>
                  </div>

                  {/* Steps */}
                  {eligibilityResult.steps.length > 0 && (
                    <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-3">
                      <h3 className="text-sm font-semibold text-gray-200">Required Steps</h3>
                      <ol className="space-y-2">
                        {eligibilityResult.steps.map((step, i) => (
                          <li key={i} className="flex gap-3 text-xs text-gray-300">
                            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-700 text-white flex items-center justify-center text-xs font-bold">
                              {i + 1}
                            </span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {/* Warnings */}
                  {eligibilityResult.warnings.length > 0 && (
                    <div className="bg-amber-900/20 border border-amber-700/40 rounded-xl p-4 space-y-2">
                      <h3 className="text-xs font-semibold text-amber-300 uppercase tracking-wide">Notices</h3>
                      {eligibilityResult.warnings.map((w, i) => (
                        <p key={i} className="text-xs text-amber-200">{w}</p>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* PENALTY CALCULATOR TAB                                               */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === "penalty" && (
          <div className="grid md:grid-cols-2 gap-6">
            <form onSubmit={handlePenaltySubmit} className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-5">
              <h2 className="text-base font-semibold text-white">SDOP Penalty Calculator</h2>
              <p className="text-xs text-gray-400">
                The SDOP miscellaneous offshore penalty is 5% of the{" "}
                <span className="text-gray-200 font-medium">highest aggregate balance</span> of unreported
                foreign financial assets across the analyzed years.
              </p>

              <div className="space-y-3">
                {penaltyYears.map((yr) => (
                  <div key={yr} className="flex items-center gap-3">
                    <span className="text-sm text-gray-400 w-12">{yr}</span>
                    <input
                      type="number"
                      min={0}
                      step="0.01"
                      placeholder="Account balance USD"
                      value={penaltyBalances[yr] ?? ""}
                      onChange={(e) =>
                        setPenaltyBalances((prev) => ({ ...prev, [yr]: e.target.value }))
                      }
                      className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setPenaltyYears((prev) => prev.filter((y) => y !== yr))
                      }
                      className="text-gray-600 hover:text-red-400 text-lg leading-none"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              {/* Add year */}
              <button
                type="button"
                onClick={() => {
                  const newYr = String(
                    (Math.max(...penaltyYears.map(Number)) || new Date().getFullYear()) + 1
                  );
                  if (!penaltyYears.includes(newYr)) {
                    setPenaltyYears((prev) => [...prev, newYr]);
                    setPenaltyBalances((prev) => ({ ...prev, [newYr]: "" }));
                  }
                }}
                className="w-full border border-dashed border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 rounded-lg py-2 text-sm transition-colors"
              >
                + Add year
              </button>

              <button
                type="submit"
                disabled={loading || penaltyYears.length === 0}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
              >
                {loading ? "Calculating…" : "Calculate Penalty"}
              </button>
            </form>

            {/* Penalty result */}
            <div className="space-y-4">
              {!penaltyResult && (
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 flex flex-col items-center justify-center h-64 text-gray-500 text-sm">
                  <svg className="w-10 h-10 mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Enter account balances to calculate the SDOP penalty
                </div>
              )}

              {penaltyResult && (
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-4">
                  <h3 className="text-sm font-semibold text-gray-200">Penalty Calculation</h3>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <Stat label="Highest Balance" value={usd(penaltyResult.highest_aggregate_balance)} />
                    <Stat label="Penalty Rate" value={`${(penaltyResult.penalty_rate * 100).toFixed(0)}%`} highlight="amber" />
                  </div>

                  <div className="bg-amber-900/20 border border-amber-700 rounded-xl p-4 text-center">
                    <p className="text-xs text-amber-400 uppercase tracking-widest mb-1">SDOP Penalty Amount</p>
                    <p className="text-3xl font-bold text-amber-300">{usd(penaltyResult.penalty_amount)}</p>
                  </div>

                  <p className="text-xs text-gray-400 leading-relaxed">{penaltyResult.explanation}</p>

                  <p className="text-xs text-gray-600">
                    Years analyzed: {penaltyResult.years_analyzed.join(", ")}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Info footer */}
        <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-5">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Quick Reference
          </h3>
          <div className="grid sm:grid-cols-2 gap-4 text-xs text-gray-400">
            <div>
              <p className="text-gray-200 font-medium mb-1">SFOP — Foreign Offshore</p>
              <ul className="space-y-0.5 list-disc list-inside">
                <li>≤ 35 days/year in US (all 3 years)</li>
                <li>Non-willful certification (Form 14653)</li>
                <li>0% penalty</li>
                <li>3 amended returns + 6 FBARs</li>
              </ul>
            </div>
            <div>
              <p className="text-gray-200 font-medium mb-1">SDOP — Domestic Offshore</p>
              <ul className="space-y-0.5 list-disc list-inside">
                <li>Does NOT meet SFOP residency test</li>
                <li>Non-willful certification (Form 14654)</li>
                <li>5% penalty on highest aggregate balance</li>
                <li>3 amended returns + 6 FBARs</li>
              </ul>
            </div>
          </div>
          <p className="text-xs text-gray-600 mt-3">
            This tool is for informational purposes only. Consult a qualified tax attorney before
            making any filings. Rev. Proc. 2014-55.
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Small stat card
// ---------------------------------------------------------------------------
function Stat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "green" | "amber";
}) {
  const valueClass =
    highlight === "green"
      ? "text-emerald-400 font-semibold"
      : highlight === "amber"
      ? "text-amber-300 font-semibold"
      : "text-white";
  return (
    <div className="bg-gray-800/60 rounded-lg px-3 py-2">
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className={`text-sm ${valueClass}`}>{value}</p>
    </div>
  );
}
