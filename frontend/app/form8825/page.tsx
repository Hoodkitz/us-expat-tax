"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiForm8825FilingRequirement,
  apiForm8825PenaltyCalculation,
  apiForm8825Overview,
  TenantOut,
  FilingRequirement8825Result,
  PenaltyResult8825,
  Form8825Overview,
} from "@/lib/api";

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

type ActiveTab = "filing" | "penalties" | "overview";

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

export default function Form8825Page() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [authError, setAuthError] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>("filing");

  // Filing Requirement State
  const [entityType, setEntityType] = useState("individual");
  const [ownershipPercent, setOwnershipPercent] = useState(0);
  const [usOwners, setUsOwners] = useState(1);
  const [foreignCorporation, setForeignCorporation] = useState<"yes" | "no">("no");
  const [taxYear, setTaxYear] = useState(new Date().getFullYear() - 1);
  const [filingResult, setFilingResult] = useState<FilingRequirement8825Result | null>(null);

  // Penalty State
  const [penaltyEntityType, setPenaltyEntityType] = useState("individual");
  const [penaltyOwnershipPercent, setPenaltyOwnershipPercent] = useState(0);
  const [penaltyUsOwners, setPenaltyUsOwners] = useState(1);
  const [penaltyForeignCorporation, setPenaltyForeignCorporation] = useState<"yes" | "no">("no");
  const [penaltyTaxYear, setPenaltyTaxYear] = useState(new Date().getFullYear() - 1);
  const [isGeneralPartner, setIsGeneralPartner] = useState(false);
  const [violationsCount, setViolationsCount] = useState(1);
  const [daysUnreported, setDaysUnreported] = useState(0);
  const [penaltyResult, setPenaltyResult] = useState<PenaltyResult8825 | null>(null);

  // Overview
  const [overview, setOverview] = useState<Form8825Overview | null>(null);

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
    apiForm8825Overview()
      .then(setOverview)
      .catch(() => {
        // Overview is non-critical
      });
  }, []);

  // Handlers
  const checkFilingRequirement = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiForm8825FilingRequirement({
        entity_type: entityType as any,
        ownership_percent: ownershipPercent,
        us_owners: usOwners,
        foreign_corporation: foreignCorporation,
        tax_year: taxYear,
      });
      setFilingResult(data);
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
      const data = await apiForm8825PenaltyCalculation({
        entity_type: penaltyEntityType as any,
        ownership_percent: penaltyOwnershipPercent,
        us_owners: penaltyUsOwners,
        foreign_corporation: penaltyForeignCorporation,
        tax_year: penaltyTaxYear,
        is_general_partner: isGeneralPartner,
        violations_count: violationsCount,
        days_unreported: daysUnreported,
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
          <p className="text-gray-600 mb-4">Please log in to access the Form 8825 Assistant.</p>
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
              Form 8825: Foreign Partnerships
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

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entity Type
                  </label>
                  <select
                    value={entityType}
                    onChange={(e) => setEntityType(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="individual">Individual</option>
                    <option value="corporation">Corporation</option>
                    <option value="partnership">Partnership</option>
                    <option value="trust">Trust</option>
                    <option value="estate">Estate</option>
                    <option value="llc">LLC</option>
                  </select>
                </div>
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
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ownership % (0-100)
                  </label>
                  <input
                    type="number"
                    value={ownershipPercent}
                    onChange={(e) => setOwnershipPercent(Number(e.target.value))}
                    min={0}
                    max={100}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Number of U.S. Owners
                  </label>
                  <input
                    type="number"
                    value={usOwners}
                    onChange={(e) => setUsOwners(Number(e.target.value))}
                    min={0}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={foreignCorporation === "yes"}
                    onChange={(e) =>
                      setForeignCorporation(e.target.checked ? "yes" : "no")
                    }
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Foreign Corporation</span>
                </label>
              </div>

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

                  {filingResult.related_forms && filingResult.related_forms.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Related Forms</h3>
                      <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                        {filingResult.related_forms.map((f, i) => (
                          <li key={i}>{f}</li>
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
                  Fill out the form and click &quot;Check Filing Requirement&quot; to see if Form 8825 is required.
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

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entity Type
                  </label>
                  <select
                    value={penaltyEntityType}
                    onChange={(e) => setPenaltyEntityType(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="individual">Individual</option>
                    <option value="corporation">Corporation</option>
                    <option value="partnership">Partnership</option>
                    <option value="trust">Trust</option>
                    <option value="estate">Estate</option>
                    <option value="llc">LLC</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tax Year
                  </label>
                  <input
                    type="number"
                    value={penaltyTaxYear}
                    onChange={(e) => setPenaltyTaxYear(Number(e.target.value))}
                    min={2000}
                    max={2099}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ownership %
                  </label>
                  <input
                    type="number"
                    value={penaltyOwnershipPercent}
                    onChange={(e) => setPenaltyOwnershipPercent(Number(e.target.value))}
                    min={0}
                    max={100}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    U.S. Owners
                  </label>
                  <input
                    type="number"
                    value={penaltyUsOwners}
                    onChange={(e) => setPenaltyUsOwners(Number(e.target.value))}
                    min={0}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Violations Count
                  </label>
                  <input
                    type="number"
                    value={violationsCount}
                    onChange={(e) => setViolationsCount(Number(e.target.value))}
                    min={1}
                    max={10}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Days Unreported
                  </label>
                  <input
                    type="number"
                    value={daysUnreported}
                    onChange={(e) => setDaysUnreported(Number(e.target.value))}
                    min={0}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mb-4 space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={penaltyForeignCorporation === "yes"}
                    onChange={(e) =>
                      setPenaltyForeignCorporation(e.target.checked ? "yes" : "no")
                    }
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Foreign Corporation</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isGeneralPartner}
                    onChange={(e) => setIsGeneralPartner(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">General Partner</span>
                </label>
              </div>

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

            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-2">Who Must File</h3>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {overview.who_must_file.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Ownership Threshold</h3>
                <p className="text-sm text-blue-800">{overview.ownership_threshold}</p>
              </div>
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="font-medium text-green-900 mb-2">Control Threshold</h3>
                <p className="text-sm text-green-800">{overview.control_threshold}</p>
              </div>
              <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                <h3 className="font-medium text-purple-900 mb-2">General Partner Rule</h3>
                <p className="text-sm text-purple-800">{overview.general_partner_rule}</p>
              </div>
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="font-medium text-red-900 mb-2">Penalties</h3>
                <p className="text-sm text-red-800">{overview.penalties}</p>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-2">Related Forms</h3>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {overview.related_forms.map((form, i) => (
                  <li key={i}>{form}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-2">Filing Deadline</h3>
              <p className="text-sm text-gray-700">{overview.filing_deadline}</p>
            </div>

            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="font-medium text-yellow-900 mb-2">Recommendation</h3>
              <p className="text-sm text-yellow-800">{overview.recommendation}</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
