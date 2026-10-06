"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiForm8865FilingRequirement,
  apiForm8865IncomeSummary,
  apiForm8865PenaltyCalculation,
  apiForm8865Overview,
  TenantOut,
  Partnership8865,
  FilingRequirement8865Result,
  IncomeSummary8865Result,
  PenaltyResult8865,
  Form8865Overview,
} from "@/lib/api";

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

type ActiveTab = "filing" | "income" | "penalties" | "overview";

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function fmtUSD(val: number | undefined): string {
  if (val === undefined || val === null) return "–";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(val);
}

// -----------------------------------------------------------------------
// Main Page Component
// -----------------------------------------------------------------------

export default function Form8865Page() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [authError, setAuthError] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>("filing");

  // Filing Requirement State
  const [taxYear, setTaxYear] = useState(new Date().getFullYear() - 1);
  const [partnerships, setPartnerships] = useState<Partnership8865[]>([
    {
      name: "",
      country: "",
      ownership_percentage: 0,
      us_controlled: false,
      fair_market_value_usd: 0,
      capital_contributed_usd: 0,
      reportable_event: false,
    },
  ]);
  const [filingResult, setFilingResult] = useState<FilingRequirement8865Result | null>(null);

  // Income Summary State
  const [partnershipName, setPartnershipName] = useState("");
  const [subpartF, setSubpartF] = useState(0);
  const [gilti, setGilti] = useState(0);
  const [qbi, setQbi] = useState(0);
  const [ordinaryIncome, setOrdinaryIncome] = useState(0);
  const [capitalGain, setCapitalGain] = useState(0);
  const [foreignTax, setForeignTax] = useState(0);
  const [incomeResult, setIncomeResult] = useState<IncomeSummary8865Result | null>(null);

  // Penalty State
  const [penaltyTaxYear, setPenaltyTaxYear] = useState(new Date().getFullYear() - 1);
  const [penaltyPartnerships, setPenaltyPartnerships] = useState<Partnership8865[]>([
    {
      name: "",
      country: "",
      ownership_percentage: 0,
      us_controlled: false,
      fair_market_value_usd: 0,
    },
  ]);
  const [daysUnreported, setDaysUnreported] = useState(0);
  const [isWillful, setIsWillful] = useState(false);
  const [penaltyResult, setPenaltyResult] = useState<PenaltyResult8865 | null>(null);

  // Overview
  const [overview, setOverview] = useState<Form8865Overview | null>(null);

  // Loading & Error
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
      });
  }, [router]);

  // ---- Load overview on mount ----
  useEffect(() => {
    apiForm8865Overview()
      .then(setOverview)
      .catch(() => {
        // Overview is non-critical
      });
  }, []);

  // Handlers
  const addPartnership = () => {
    setPartnerships([
      ...partnerships,
      {
        name: "",
        country: "",
        ownership_percentage: 0,
        us_controlled: false,
        fair_market_value_usd: 0,
        capital_contributed_usd: 0,
        reportable_event: false,
      },
    ]);
  };

  const removePartnership = (index: number) => {
    setPartnerships(partnerships.filter((_, i) => i !== index));
  };

  const updatePartnership = (index: number, field: keyof Partnership8865, value: any) => {
    const updated = [...partnerships];
    (updated[index] as any)[field] = value;
    setPartnerships(updated);
  };

  const addPenaltyPartnership = () => {
    setPenaltyPartnerships([
      ...penaltyPartnerships,
      {
        name: "",
        country: "",
        ownership_percentage: 0,
        us_controlled: false,
        fair_market_value_usd: 0,
      },
    ]);
  };

  const removePenaltyPartnership = (index: number) => {
    setPenaltyPartnerships(penaltyPartnerships.filter((_, i) => i !== index));
  };

  const updatePenaltyPartnership = (index: number, field: keyof Partnership8865, value: any) => {
    const updated = [...penaltyPartnerships];
    (updated[index] as any)[field] = value;
    setPenaltyPartnerships(updated);
  };

  const checkFilingRequirement = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiForm8865FilingRequirement({
        tax_year: taxYear,
        partnerships: partnerships,
      });
      setFilingResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const summarizeIncome = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiForm8865IncomeSummary({
        tax_year: taxYear,
        partnership_name: partnershipName,
        subpart_f_income_usd: subpartF,
        gilti_usd: gilti,
        qbi_199a_usd: qbi,
        ordinary_income_usd: ordinaryIncome,
        capital_gain_usd: capitalGain,
        foreign_tax_paid_usd: foreignTax,
      });
      setIncomeResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const calculatePenalty = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiForm8865PenaltyCalculation({
        tax_year: penaltyTaxYear,
        partnerships: penaltyPartnerships,
        days_unreported: daysUnreported,
        is_willful: isWillful,
      });
      setPenaltyResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  if (authError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          <h2 className="text-xl font-bold text-red-600 mb-4">Authentication Required</h2>
          <p className="text-gray-600 mb-4">Please log in to access the Form 8865 Assistant.</p>
          <Link
            href="/auth/login"
            className="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-blue-600 hover:text-blue-800">
              ← Back to Dashboard
            </Link>
            <h1 className="text-xl font-bold text-gray-900">
              Form 8865: Foreign Partnerships
            </h1>
          </div>
          <div className="text-sm text-gray-500">
            {tenant.tenant_name}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 border-b">
          <button
            onClick={() => setActiveTab("filing")}
            className={`px-4 py-2 font-medium text-sm rounded-t-lg ${
              activeTab === "filing"
                ? "bg-white text-blue-600 border border-b-white"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Filing Requirement
          </button>
          <button
            onClick={() => setActiveTab("income")}
            className={`px-4 py-2 font-medium text-sm rounded-t-lg ${
              activeTab === "income"
                ? "bg-white text-blue-600 border border-b-white"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Income Summary
          </button>
          <button
            onClick={() => setActiveTab("penalties")}
            className={`px-4 py-2 font-medium text-sm rounded-t-lg ${
              activeTab === "penalties"
                ? "bg-white text-blue-600 border border-b-white"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Penalties
          </button>
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 font-medium text-sm rounded-t-lg ${
              activeTab === "overview"
                ? "bg-white text-blue-600 border border-b-white"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Overview
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Filing Requirement Tab */}
        {activeTab === "filing" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Form */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4">Check Filing Requirement</h2>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tax Year
                </label>
                <input
                  type="number"
                  value={taxYear}
                  onChange={(e) => setTaxYear(Number(e.target.value))}
                  min={2000}
                  max={2099}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <h3 className="text-md font-semibold text-gray-800 mb-3">
                Partnerships
              </h3>

              {partnerships.map((p, idx) => (
                <div key={idx} className="mb-4 p-4 bg-gray-50 rounded-lg">
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Partnership Name
                      </label>
                      <input
                        type="text"
                        value={p.name}
                        onChange={(e) =>
                          updatePartnership(idx, "name", e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Country
                      </label>
                      <input
                        type="text"
                        value={p.country}
                        onChange={(e) =>
                          updatePartnership(idx, "country", e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Ownership % (0-100)
                      </label>
                      <input
                        type="number"
                        value={p.ownership_percentage}
                        onChange={(e) =>
                          updatePartnership(
                            idx,
                            "ownership_percentage",
                            Number(e.target.value)
                          )
                        }
                        min={0}
                        max={100}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Fair Market Value (USD)
                      </label>
                      <input
                        type="number"
                        value={p.fair_market_value_usd}
                        onChange={(e) =>
                          updatePartnership(
                            idx,
                            "fair_market_value_usd",
                            Number(e.target.value)
                          )
                        }
                        min={0}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Capital Contributed (USD)
                      </label>
                      <input
                        type="number"
                        value={p.capital_contributed_usd || 0}
                        onChange={(e) =>
                          updatePartnership(
                            idx,
                            "capital_contributed_usd",
                            Number(e.target.value)
                          )
                        }
                        min={0}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={p.us_controlled}
                        onChange={(e) =>
                          updatePartnership(
                            idx,
                            "us_controlled",
                            e.target.checked
                          )
                        }
                        className="mr-1"
                      />
                      U.S.-Controlled
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={p.reportable_event || false}
                        onChange={(e) =>
                          updatePartnership(
                            idx,
                            "reportable_event",
                            e.target.checked
                          )
                        }
                        className="mr-1"
                      />
                      Reportable Event
                    </label>
                    {partnerships.length > 1 && (
                      <button
                        onClick={() => removePartnership(idx)}
                        className="ml-auto px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              ))}

              <button
                onClick={addPartnership}
                className="mb-4 px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
              >
                + Add Partnership
              </button>

              <button
                onClick={checkFilingRequirement}
                disabled={loading}
                className="w-full py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Checking..." : "Check Filing Requirement"}
              </button>
            </div>

            {/* Result */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4">Result</h2>
              {filingResult ? (
                <div className="space-y-4">
                  <div
                    className={`p-4 rounded-lg ${
                      filingResult.filing_required
                        ? "bg-green-50 border border-green-200"
                        : "bg-yellow-50 border border-yellow-200"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`text-2xl ${
                          filingResult.filing_required ? "text-green-600" : "text-yellow-600"
                        }`}
                      >
                        {filingResult.filing_required ? "✓" : "⚠"}
                      </span>
                      <span
                        className={`font-semibold ${
                          filingResult.filing_required ? "text-green-800" : "text-yellow-800"
                        }`}
                      >
                        {filingResult.filing_required
                          ? "Filing Required"
                          : "Filing Not Required"}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{filingResult.recommendation}</p>
                  </div>

                  {filingResult.categories && filingResult.categories.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Categories Triggered</h3>
                      <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                        {filingResult.categories.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {filingResult.reasons && filingResult.reasons.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Reasons</h3>
                      <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                        {filingResult.reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="pt-4 border-t">
                    <p className="text-sm text-gray-700">
                      <strong>Penalty if Not Filed:</strong> {fmtUSD(filingResult.penalty_if_not_filed)}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 text-sm">
                  Fill out the form and click &quot;Check Filing Requirement&quot; to see if Form 8865 is required.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Income Summary Tab */}
        {activeTab === "income" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4">Income Summary</h2>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tax Year
                  </label>
                  <input
                    type="number"
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    min={2000}
                    max={2099}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Partnership Name
                  </label>
                  <input
                    type="text"
                    value={partnershipName}
                    onChange={(e) => setPartnershipName(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subpart F Income (USD)
                  </label>
                  <input
                    type="number"
                    value={subpartF}
                    onChange={(e) => setSubpartF(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    GILTI (USD)
                  </label>
                  <input
                    type="number"
                    value={gilti}
                    onChange={(e) => setGilti(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    QBI (§199A) (USD)
                  </label>
                  <input
                    type="number"
                    value={qbi}
                    onChange={(e) => setQbi(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ordinary Income (USD)
                  </label>
                  <input
                    type="number"
                    value={ordinaryIncome}
                    onChange={(e) => setOrdinaryIncome(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Capital Gain (USD)
                  </label>
                  <input
                    type="number"
                    value={capitalGain}
                    onChange={(e) => setCapitalGain(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Foreign Tax Paid (USD)
                  </label>
                  <input
                    type="number"
                    value={foreignTax}
                    onChange={(e) => setForeignTax(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>

              <button
                onClick={summarizeIncome}
                disabled={loading}
                className="w-full py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Calculating..." : "Summarize Income"}
              </button>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4">Result</h2>
              {incomeResult ? (
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm mb-2">
                      <strong>Total Income:</strong> {fmtUSD(incomeResult.total_income_usd)}
                    </p>
                    <p className="text-sm mb-2">
                      <strong>Foreign Tax Credit Eligible:</strong>{" "}
                      {incomeResult.foreign_tax_credit_eligible ? "Yes" : "No"}
                    </p>
                  </div>
                  {incomeResult.notes && incomeResult.notes.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Notes</h3>
                      <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                        {incomeResult.notes.map((n, i) => (
                          <li key={i}>{n}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">
                  Fill out the form and click &quot;Summarize Income&quot; to see partnership income breakdown.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Penalties Tab */}
        {activeTab === "penalties" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4">Penalty Calculation</h2>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tax Year
                </label>
                <input
                  type="number"
                  value={penaltyTaxYear}
                  onChange={(e) => setPenaltyTaxYear(Number(e.target.value))}
                  min={2000}
                  max={2099}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Days Unreported
                </label>
                <input
                  type="number"
                  value={daysUnreported}
                  onChange={(e) => setDaysUnreported(Number(e.target.value))}
                  min={0}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>

              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isWillful}
                    onChange={(e) => setIsWillful(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Willful Failure</span>
                </label>
              </div>

              <h3 className="text-md font-semibold text-gray-800 mb-3">Partnerships</h3>

              {penaltyPartnerships.map((p, idx) => (
                <div key={idx} className="mb-4 p-4 bg-gray-50 rounded-lg">
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Name
                      </label>
                      <input
                        type="text"
                        value={p.name}
                        onChange={(e) =>
                          updatePenaltyPartnership(idx, "name", e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Country
                      </label>
                      <input
                        type="text"
                        value={p.country}
                        onChange={(e) =>
                          updatePenaltyPartnership(idx, "country", e.target.value)
                        }
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Ownership %
                      </label>
                      <input
                        type="number"
                        value={p.ownership_percentage}
                        onChange={(e) =>
                          updatePenaltyPartnership(
                            idx,
                            "ownership_percentage",
                            Number(e.target.value)
                          )
                        }
                        min={0}
                        max={100}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        FMV (USD)
                      </label>
                      <input
                        type="number"
                        value={p.fair_market_value_usd}
                        onChange={(e) =>
                          updatePenaltyPartnership(
                            idx,
                            "fair_market_value_usd",
                            Number(e.target.value)
                          )
                        }
                        min={0}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={p.us_controlled}
                        onChange={(e) =>
                          updatePenaltyPartnership(idx, "us_controlled", e.target.checked)
                        }
                        className="mr-1"
                      />
                      U.S.-Controlled
                    </label>
                    {penaltyPartnerships.length > 1 && (
                      <button
                        onClick={() => removePenaltyPartnership(idx)}
                        className="ml-auto px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              ))}

              <button
                onClick={addPenaltyPartnership}
                className="mb-4 px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
              >
                + Add Partnership
              </button>

              <button
                onClick={calculatePenalty}
                disabled={loading}
                className="w-full py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Calculating..." : "Calculate Penalty"}
              </button>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-lg font-semibold mb-4">Result</h2>
              {penaltyResult ? (
                <div className="space-y-4">
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm mb-2">
                      <strong>Base Penalty:</strong> {fmtUSD(penaltyResult.base_penalty)}
                    </p>
                    <p className="text-sm mb-2">
                      <strong>Continued Failure Penalty:</strong> {fmtUSD(penaltyResult.continued_failure_penalty)}
                    </p>
                    {penaltyResult.willful_penalty > 0 && (
                      <p className="text-sm mb-2">
                        <strong>Willful Penalty:</strong> {fmtUSD(penaltyResult.willful_penalty)}
                      </p>
                    )}
                    <p className="text-lg font-bold mt-3">
                      <strong>Total Penalty:</strong> {fmtUSD(penaltyResult.total_penalty)}
                    </p>
                  </div>
                  <p className="text-sm text-gray-700">{penaltyResult.explanation}</p>
                </div>
              ) : (
                <p className="text-gray-500 text-sm">
                  Fill out the form and click &quot;Calculate Penalty&quot; to see potential penalties.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === "overview" && overview && (
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-xl font-bold text-gray-900 mb-4">{overview.title}</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Category 1</h3>
                <p className="text-sm text-blue-800">{overview.category_1}</p>
              </div>

              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="font-medium text-green-900 mb-2">Category 2</h3>
                <p className="text-sm text-green-800">{overview.category_2}</p>
              </div>

              <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                <h3 className="font-medium text-purple-900 mb-2">Category 3</h3>
                <p className="text-sm text-purple-800">{overview.category_3}</p>
              </div>

              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <h3 className="font-medium text-orange-900 mb-2">Category 4</h3>
                <p className="text-sm text-orange-800">{overview.category_4}</p>
              </div>

              <div className="p-4 bg-pink-50 border border-pink-200 rounded-lg">
                <h3 className="font-medium text-pink-900 mb-2">Category 5</h3>
                <p className="text-sm text-pink-800">{overview.category_5}</p>
              </div>

              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="font-medium text-red-900 mb-2">Penalties</h3>
                <p className="text-sm text-red-800">{overview.penalties}</p>
              </div>
            </div>

            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-2">Filing Deadline</h3>
              <p className="text-sm text-gray-700">{overview.filing_deadline}</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
