"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

// -----------------------------------------------------------------------
// Type Definitions
// -----------------------------------------------------------------------

interface TenantOut {
  email: string;
  tenant_id: string;
  tenant_name: string;
}

interface ExtensionResult {
  extended_deadline: string;
  days_extended: number;
  extension_granted: boolean;
  balance_due: string;
  payment_deadline: string;
  penalty_if_not_filed: string;
  interest_if_not_paid: string;
  explanation: string;
}

interface ExtensionStatusResult {
  extension_filed: boolean;
  filing_status: string;
  payment_status: string;
  days_remaining: number;
  extended_deadline: string;
}

interface AbroadCheckResult {
  eligible: boolean;
  automatic_extension: {
    deadline: string;
    description: string;
  };
  extended_deadline: string;
  requirements: string[];
}

interface Form4868Overview {
  form: string;
  title: string;
  purpose: string;
  key_facts: string[];
  deadlines: {
    original: string;
    extended: string;
    abroad_automatic: string;
  };
  penalties: {
    failure_to_file: string;
    failure_to_pay: string;
    interest: string;
  };
  special_rules: string[];
  how_to_file: string[];
  statutory_references: string[];
  irs_reference: string;
}

// -----------------------------------------------------------------------
// API Functions
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

async function apiCalculate(payload: {
  filing_status: string;
  tax_year: number;
  original_deadline: string;
  extension_months: number;
  estimated_tax_liability: string;
  amount_paid: string;
}): Promise<ExtensionResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/form4868/calculate`, {
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

async function apiStatus(payload: {
  extension_filed: boolean;
  tax_year: number;
}): Promise<ExtensionStatusResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/form4868/status`, {
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

async function apiAbroadCheck(payload: {
  country: string;
  tax_year: number;
  living_abroad: boolean;
}): Promise<AbroadCheckResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/form4868/abroad-check`, {
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

async function apiOverview(): Promise<Form4868Overview> {
  const res = await fetch(`${API_BASE}/api/v1/form4868/overview`);
  if (!res.ok) throw new Error("API request failed");
  return res.json();
}

// -----------------------------------------------------------------------
// Component
// -----------------------------------------------------------------------

export default function Form4868Page() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtensionResult | null>(null);
  const [statusResult, setStatusResult] = useState<ExtensionStatusResult | null>(null);
  const [abroadResult, setAbroadResult] = useState<AbroadCheckResult | null>(null);
  const [overview, setOverview] = useState<Form4868Overview | null>(null);
  const [activeTab, setActiveTab] = useState<"calculator" | "status" | "abroad" | "overview">("calculator");

  // Form state
  const [filingStatus, setFilingStatus] = useState("single");
  const [taxYear, setTaxYear] = useState(2025);
  const [originalDeadline, setOriginalDeadline] = useState("2025-04-15");
  const [extensionMonths, setExtensionMonths] = useState(6);
  const [estimatedTaxLiability, setEstimatedTaxLiability] = useState("");
  const [amountPaid, setAmountPaid] = useState("");

  // Status form state
  const [extensionFiled, setExtensionFiled] = useState(false);

  // Abroad form state
  const [country, setCountry] = useState("");
  const [livingAbroad, setLivingAbroad] = useState(false);

  useEffect(() => {
    apiMe()
      .then(setTenant)
      .catch(() => router.push("/login"));
  }, [router]);

  useEffect(() => {
    apiOverview()
      .then(setOverview)
      .catch(console.error);
  }, []);

  async function handleCalculate(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const calcResult = await apiCalculate({
        filing_status: filingStatus,
        tax_year: taxYear,
        original_deadline: originalDeadline,
        extension_months: extensionMonths,
        estimated_tax_liability: estimatedTaxLiability,
        amount_paid: amountPaid,
      });
      setResult(calcResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Calculation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleStatus(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setStatusResult(null);

    try {
      const statusRes = await apiStatus({
        extension_filed: extensionFiled,
        tax_year: taxYear,
      });
      setStatusResult(statusRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status check failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleAbroadCheck(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setAbroadResult(null);

    try {
      const abroadRes = await apiAbroadCheck({
        country: country,
        tax_year: taxYear,
        living_abroad: livingAbroad,
      });
      setAbroadResult(abroadRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Abroad check failed");
    } finally {
      setLoading(false);
    }
  }

  if (!tenant) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-blue-600 hover:text-blue-800">
              ← Back to Dashboard
            </Link>
            <h1 className="text-xl font-semibold text-gray-900">Form 4868</h1>
          </div>
          <div className="text-sm text-gray-600">
            {tenant.tenant_name} • {tenant.email}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {/* Tabs */}
        <div className="mb-6 flex gap-2 border-b">
          <button
            onClick={() => setActiveTab("calculator")}
            className={`px-4 py-2 font-medium ${
              activeTab === "calculator"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Extension Calculator
          </button>
          <button
            onClick={() => setActiveTab("status")}
            className={`px-4 py-2 font-medium ${
              activeTab === "status"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Status Check
          </button>
          <button
            onClick={() => setActiveTab("abroad")}
            className={`px-4 py-2 font-medium ${
              activeTab === "abroad"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Abroad Extension
          </button>
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 font-medium ${
              activeTab === "overview"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Overview
          </button>
        </div>

        {/* Calculator Tab */}
        {activeTab === "calculator" && (
          <div className="grid gap-8 lg:grid-cols-2">
            {/* Form */}
            <div className="rounded-lg bg-white p-6 shadow">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">
                Extension Calculator
              </h2>
              <form onSubmit={handleCalculate} className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Filing Status
                  </label>
                  <select
                    value={filingStatus}
                    onChange={(e) => setFilingStatus(e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  >
                    <option value="single">Single</option>
                    <option value="married_joint">Married Filing Jointly</option>
                    <option value="married_separate">Married Filing Separately</option>
                    <option value="head_of_household">Head of Household</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Tax Year
                  </label>
                  <select
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  >
                    <option value={2023}>2023</option>
                    <option value={2024}>2024</option>
                    <option value={2025}>2025</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Original Deadline
                  </label>
                  <input
                    type="date"
                    value={originalDeadline}
                    onChange={(e) => setOriginalDeadline(e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Extension Months
                  </label>
                  <select
                    value={extensionMonths}
                    onChange={(e) => setExtensionMonths(Number(e.target.value))}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  >
                    <option value={6}>6 months (standard)</option>
                    <option value={4}>4 months</option>
                    <option value={2}>2 months (abroad automatic)</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Estimated Tax Liability ($)
                  </label>
                  <input
                    type="number"
                    value={estimatedTaxLiability}
                    onChange={(e) => setEstimatedTaxLiability(e.target.value)}
                    placeholder="e.g., 15000"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Amount Already Paid ($)
                  </label>
                  <input
                    type="number"
                    value={amountPaid}
                    onChange={(e) => setAmountPaid(e.target.value)}
                    placeholder="e.g., 5000"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "Calculating..." : "Calculate Extension"}
                </button>
              </form>
            </div>

            {/* Results */}
            <div className="space-y-6">
              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
                  {error}
                </div>
              )}

              {result && (
                <div className="rounded-lg bg-white p-6 shadow">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">Results</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Extended Deadline</span>
                      <span className="font-medium">{result.extended_deadline}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Days Extended</span>
                      <span className="font-medium">{result.days_extended}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Extension Granted</span>
                      <span
                        className={`font-medium ${
                          result.extension_granted ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {result.extension_granted ? "Yes" : "No"}
                      </span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Balance Due</span>
                      <span className="font-medium text-red-600">${result.balance_due}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Payment Deadline</span>
                      <span className="font-medium">{result.payment_deadline}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Penalty if Not Filed</span>
                      <span className="font-medium text-red-600">
                        ${result.penalty_if_not_filed}
                      </span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Interest if Not Paid</span>
                      <span className="font-medium text-red-600">
                        ${result.interest_if_not_paid}
                      </span>
                    </div>
                  </div>
                  <div className="mt-4 rounded bg-blue-50 p-3 text-sm text-blue-800">
                    {result.explanation}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Status Tab */}
        {activeTab === "status" && (
          <div className="grid gap-8 lg:grid-cols-2">
            <div className="rounded-lg bg-white p-6 shadow">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">
                Extension Status Check
              </h2>
              <form onSubmit={handleStatus} className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Extension Filed?
                  </label>
                  <select
                    value={extensionFiled ? "yes" : "no"}
                    onChange={(e) => setExtensionFiled(e.target.value === "yes")}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  >
                    <option value="no">No</option>
                    <option value="yes">Yes</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Tax Year
                  </label>
                  <select
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  >
                    <option value={2023}>2023</option>
                    <option value={2024}>2024</option>
                    <option value={2025}>2025</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "Checking..." : "Check Status"}
                </button>
              </form>
            </div>

            <div>
              {statusResult && (
                <div className="rounded-lg bg-white p-6 shadow">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">Status</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Extension Filed</span>
                      <span
                        className={`font-medium ${
                          statusResult.extension_filed ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {statusResult.extension_filed ? "Yes" : "No"}
                      </span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Filing Status</span>
                      <span className="font-medium">{statusResult.filing_status}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Payment Status</span>
                      <span className="font-medium">{statusResult.payment_status}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Days Remaining</span>
                      <span
                        className={`font-medium ${
                          statusResult.days_remaining > 0 ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {statusResult.days_remaining}
                      </span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Extended Deadline</span>
                      <span className="font-medium">{statusResult.extended_deadline}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Abroad Tab */}
        {activeTab === "abroad" && (
          <div className="grid gap-8 lg:grid-cols-2">
            <div className="rounded-lg bg-white p-6 shadow">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">
                Abroad Extension Eligibility
              </h2>
              <form onSubmit={handleAbroadCheck} className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Country of Residence
                  </label>
                  <input
                    type="text"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    placeholder="e.g., Germany"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Living Abroad?
                  </label>
                  <select
                    value={livingAbroad ? "yes" : "no"}
                    onChange={(e) => setLivingAbroad(e.target.value === "yes")}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  >
                    <option value="no">No</option>
                    <option value="yes">Yes</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Tax Year
                  </label>
                  <select
                    value={taxYear}
                    onChange={(e) => setTaxYear(Number(e.target.value))}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  >
                    <option value={2023}>2023</option>
                    <option value={2024}>2024</option>
                    <option value={2025}>2025</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "Checking..." : "Check Eligibility"}
                </button>
              </form>
            </div>

            <div>
              {abroadResult && (
                <div className="rounded-lg bg-white p-6 shadow">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">Result</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Eligible</span>
                      <span
                        className={`font-medium ${
                          abroadResult.eligible ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {abroadResult.eligible ? "Yes" : "No"}
                      </span>
                    </div>
                    {abroadResult.eligible && (
                      <>
                        <div className="flex justify-between border-b pb-2">
                          <span className="text-gray-600">Automatic Extension Deadline</span>
                          <span className="font-medium">
                            {abroadResult.automatic_extension.deadline}
                          </span>
                        </div>
                        <div className="flex justify-between border-b pb-2">
                          <span className="text-gray-600">Extended Deadline</span>
                          <span className="font-medium">{abroadResult.extended_deadline}</span>
                        </div>
                      </>
                    )}
                  </div>
                  {abroadResult.requirements.length > 0 && (
                    <div className="mt-4">
                      <h4 className="mb-2 font-medium text-gray-900">Requirements</h4>
                      <ul className="list-inside list-disc space-y-1 text-sm text-gray-700">
                        {abroadResult.requirements.map((req, i) => (
                          <li key={i}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === "overview" && overview && (
          <div className="space-y-6">
            <div className="rounded-lg bg-white p-6 shadow">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">
                {overview.title}
              </h2>
              <p className="mb-4 text-gray-700">{overview.purpose}</p>

              <h3 className="mb-2 font-medium text-gray-900">Key Facts</h3>
              <ul className="mb-4 list-inside list-disc space-y-1 text-gray-700">
                {overview.key_facts.map((fact, i) => (
                  <li key={i}>{fact}</li>
                ))}
              </ul>

              <h3 className="mb-2 font-medium text-gray-900">Deadlines</h3>
              <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
                <div className="rounded border p-3">
                  <div className="font-medium">Original</div>
                  <div className="text-sm text-gray-600">{overview.deadlines.original}</div>
                </div>
                <div className="rounded border p-3">
                  <div className="font-medium">Extended</div>
                  <div className="text-sm text-gray-600">{overview.deadlines.extended}</div>
                </div>
                <div className="rounded border p-3">
                  <div className="font-medium">Abroad Automatic</div>
                  <div className="text-sm text-gray-600">
                    {overview.deadlines.abroad_automatic}
                  </div>
                </div>
              </div>

              <h3 className="mb-2 font-medium text-gray-900">Penalties</h3>
              <div className="mb-4 space-y-2">
                <div className="rounded bg-red-50 p-3">
                  <strong>Failure to File:</strong> {overview.penalties.failure_to_file}
                </div>
                <div className="rounded bg-red-50 p-3">
                  <strong>Failure to Pay:</strong> {overview.penalties.failure_to_pay}
                </div>
                <div className="rounded bg-yellow-50 p-3">
                  <strong>Interest:</strong> {overview.penalties.interest}
                </div>
              </div>

              <h3 className="mb-2 font-medium text-gray-900">Special Rules</h3>
              <ul className="mb-4 list-inside list-disc space-y-1 text-gray-700">
                {overview.special_rules.map((rule, i) => (
                  <li key={i}>{rule}</li>
                ))}
              </ul>

              <h3 className="mb-2 font-medium text-gray-900">How to File</h3>
              <ul className="mb-4 list-inside list-disc space-y-1 text-gray-700">
                {overview.how_to_file.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ul>

              <h3 className="mb-2 font-medium text-gray-900">Statutory References</h3>
              <ul className="list-inside list-disc space-y-1 text-gray-700">
                {overview.statutory_references.map((ref, i) => (
                  <li key={i}>{ref}</li>
                ))}
              </ul>

              <div className="mt-4 rounded bg-gray-50 p-3 text-sm text-gray-600">
                IRS Reference: {overview.irs_reference}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
