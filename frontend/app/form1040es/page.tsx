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

interface EstimatedTaxResult {
  total_tax_liability: string;
  total_payments: string;
  balance_due: string;
  quarterly_payment: string;
  safe_harbor_met: boolean;
  safe_harbor_amount: string;
  underpayment_penalty: string;
  effective_tax_rate: string;
  marginal_tax_rate: string;
  explanation: string;
}

interface QuarterlyPayment {
  quarter: number;
  due_date: string;
  amount_due: string;
  cumulative_due: string;
}

interface QuarterlyScheduleResult {
  payments: QuarterlyPayment[];
  total_due: string;
  total_paid: string;
  remaining_balance: string;
}

interface Form1040ESOverview {
  form: string;
  title: string;
  purpose: string;
  who_must_file: string[];
  safe_harbor_rules: {
    rule_1: string;
    rule_2: string;
  };
  quarterly_due_dates: {
    Q1: string;
    Q2: string;
    Q3: string;
    Q4: string;
  };
  underpayment_penalty: {
    rate: string;
    description: string;
  };
  key_rules: string[];
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
  annual_income: string;
  withholding: string;
  deductions: string;
  credits: string;
  prior_year_tax: string;
  quarters_paid: number;
  amount_paid: string;
}): Promise<EstimatedTaxResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/form1040es/calculate`, {
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

async function apiQuarterlySchedule(payload: {
  filing_status: string;
  annual_income: string;
  withholding: string;
  deductions: string;
  credits: string;
  prior_year_tax: string;
  quarters_paid: number;
  amount_paid: string;
}): Promise<QuarterlyScheduleResult> {
  const token = localStorage.getItem("jwt_token");
  const res = await fetch(`${API_BASE}/api/v1/form1040es/quarterly-schedule`, {
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

async function apiOverview(): Promise<Form1040ESOverview> {
  const res = await fetch(`${API_BASE}/api/v1/form1040es/overview`);
  if (!res.ok) throw new Error("API request failed");
  return res.json();
}

// -----------------------------------------------------------------------
// Component
// -----------------------------------------------------------------------

export default function Form1040ESPage() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EstimatedTaxResult | null>(null);
  const [scheduleResult, setScheduleResult] = useState<QuarterlyScheduleResult | null>(null);
  const [overview, setOverview] = useState<Form1040ESOverview | null>(null);
  const [activeTab, setActiveTab] = useState<"calculator" | "schedule" | "overview">("calculator");

  // Form state
  const [filingStatus, setFilingStatus] = useState("single");
  const [annualIncome, setAnnualIncome] = useState("");
  const [withholding, setWithholding] = useState("");
  const [deductions, setDeductions] = useState("");
  const [credits, setCredits] = useState("");
  const [priorYearTax, setPriorYearTax] = useState("");
  const [quartersPaid, setQuartersPaid] = useState(0);
  const [amountPaid, setAmountPaid] = useState("");

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
    setScheduleResult(null);

    try {
      const calcResult = await apiCalculate({
        filing_status: filingStatus,
        annual_income: annualIncome,
        withholding: withholding,
        deductions: deductions,
        credits: credits,
        prior_year_tax: priorYearTax,
        quarters_paid: quartersPaid,
        amount_paid: amountPaid,
      });
      setResult(calcResult);

      const schedResult = await apiQuarterlySchedule({
        filing_status: filingStatus,
        annual_income: annualIncome,
        withholding: withholding,
        deductions: deductions,
        credits: credits,
        prior_year_tax: priorYearTax,
        quarters_paid: quartersPaid,
        amount_paid: amountPaid,
      });
      setScheduleResult(schedResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Calculation failed");
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
            <h1 className="text-xl font-semibold text-gray-900">Form 1040-ES</h1>
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
            Calculator
          </button>
          <button
            onClick={() => setActiveTab("schedule")}
            className={`px-4 py-2 font-medium ${
              activeTab === "schedule"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Quarterly Schedule
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
                Estimated Tax Calculator
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
                    Annual Income ($)
                  </label>
                  <input
                    type="number"
                    value={annualIncome}
                    onChange={(e) => setAnnualIncome(e.target.value)}
                    placeholder="e.g., 85000"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Federal Withholding ($)
                  </label>
                  <input
                    type="number"
                    value={withholding}
                    onChange={(e) => setWithholding(e.target.value)}
                    placeholder="e.g., 5000"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Deductions ($)
                  </label>
                  <input
                    type="number"
                    value={deductions}
                    onChange={(e) => setDeductions(e.target.value)}
                    placeholder="e.g., 0 (standard deduction applied automatically)"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Tax Credits ($)
                  </label>
                  <input
                    type="number"
                    value={credits}
                    onChange={(e) => setCredits(e.target.value)}
                    placeholder="e.g., 0"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Prior Year Tax Liability ($)
                  </label>
                  <input
                    type="number"
                    value={priorYearTax}
                    onChange={(e) => setPriorYearTax(e.target.value)}
                    placeholder="e.g., 12000"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Quarters Already Paid
                  </label>
                  <select
                    value={quartersPaid}
                    onChange={(e) => setQuartersPaid(Number(e.target.value))}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  >
                    <option value={0}>0</option>
                    <option value={1}>1</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Amount Already Paid ($)
                  </label>
                  <input
                    type="number"
                    value={amountPaid}
                    onChange={(e) => setAmountPaid(e.target.value)}
                    placeholder="e.g., 0"
                    className="w-full rounded border border-gray-300 px-3 py-2"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "Calculating..." : "Calculate Estimated Tax"}
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
                      <span className="text-gray-600">Total Tax Liability</span>
                      <span className="font-medium">${result.total_tax_liability}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Total Payments</span>
                      <span className="font-medium">${result.total_payments}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Balance Due</span>
                      <span className="font-medium text-red-600">${result.balance_due}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Quarterly Payment</span>
                      <span className="font-medium">${result.quarterly_payment}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Safe Harbor Met</span>
                      <span
                        className={`font-medium ${
                          result.safe_harbor_met ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {result.safe_harbor_met ? "Yes" : "No"}
                      </span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Safe Harbor Amount</span>
                      <span className="font-medium">${result.safe_harbor_amount}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Underpayment Penalty</span>
                      <span className="font-medium text-red-600">
                        ${result.underpayment_penalty}
                      </span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Effective Tax Rate</span>
                      <span className="font-medium">
                        {(parseFloat(result.effective_tax_rate) * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-gray-600">Marginal Tax Rate</span>
                      <span className="font-medium">
                        {(parseFloat(result.marginal_tax_rate) * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-4 rounded bg-blue-50 p-3 text-sm text-blue-800">
                    {result.explanation}
                  </div>
                </div>
              )}

              {scheduleResult && (
                <div className="rounded-lg bg-white p-6 shadow">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">
                    Quarterly Payment Schedule
                  </h3>
                  <div className="space-y-2">
                    {scheduleResult.payments.map((payment) => (
                      <div
                        key={payment.quarter}
                        className="flex items-center justify-between rounded border p-3"
                      >
                        <div>
                          <div className="font-medium">Quarter {payment.quarter}</div>
                          <div className="text-sm text-gray-600">Due: {payment.due_date}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">${payment.amount_due}</div>
                          <div className="text-sm text-gray-600">
                            Cumulative: ${payment.cumulative_due}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex justify-between border-t pt-3">
                    <span className="font-medium">Total Due</span>
                    <span className="font-medium">${scheduleResult.total_due}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Paid</span>
                    <span>${scheduleResult.total_paid}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Remaining Balance</span>
                    <span className="font-medium text-red-600">
                      ${scheduleResult.remaining_balance}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Schedule Tab */}
        {activeTab === "schedule" && (
          <div className="rounded-lg bg-white p-6 shadow">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
              Quarterly Payment Schedule
            </h2>
            {scheduleResult ? (
              <div className="space-y-4">
                {scheduleResult.payments.map((payment) => (
                  <div
                    key={payment.quarter}
                    className="flex items-center justify-between rounded border p-4"
                  >
                    <div>
                      <div className="text-lg font-medium">Quarter {payment.quarter}</div>
                      <div className="text-sm text-gray-600">Due: {payment.due_date}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-medium">${payment.amount_due}</div>
                      <div className="text-sm text-gray-600">
                        Cumulative: ${payment.cumulative_due}
                      </div>
                    </div>
                  </div>
                ))}
                <div className="mt-6 rounded bg-gray-50 p-4">
                  <div className="flex justify-between">
                    <span className="font-medium">Total Due</span>
                    <span className="font-medium">${scheduleResult.total_due}</span>
                  </div>
                  <div className="mt-2 flex justify-between">
                    <span className="text-gray-600">Total Paid</span>
                    <span>${scheduleResult.total_paid}</span>
                  </div>
                  <div className="mt-2 flex justify-between">
                    <span className="text-gray-600">Remaining Balance</span>
                    <span className="font-medium text-red-600">
                      ${scheduleResult.remaining_balance}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-600">
                Use the Calculator tab to generate a quarterly payment schedule.
              </p>
            )}
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

              <h3 className="mb-2 font-medium text-gray-900">Who Must File</h3>
              <ul className="mb-4 list-inside list-disc space-y-1 text-gray-700">
                {overview.who_must_file.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>

              <h3 className="mb-2 font-medium text-gray-900">Safe Harbor Rules</h3>
              <div className="mb-4 space-y-2">
                <div className="rounded bg-green-50 p-3">
                  <strong>Rule 1:</strong> {overview.safe_harbor_rules.rule_1}
                </div>
                <div className="rounded bg-blue-50 p-3">
                  <strong>Rule 2:</strong> {overview.safe_harbor_rules.rule_2}
                </div>
              </div>

              <h3 className="mb-2 font-medium text-gray-900">Quarterly Due Dates</h3>
              <div className="mb-4 grid grid-cols-2 gap-2">
                {Object.entries(overview.quarterly_due_dates).map(([quarter, date]) => (
                  <div key={quarter} className="rounded border p-2">
                    <span className="font-medium">{quarter}:</span> {date}
                  </div>
                ))}
              </div>

              <h3 className="mb-2 font-medium text-gray-900">Underpayment Penalty</h3>
              <p className="mb-4 text-gray-700">
                {overview.underpayment_penalty.description} Rate:{" "}
                {overview.underpayment_penalty.rate}
              </p>

              <h3 className="mb-2 font-medium text-gray-900">Key Rules</h3>
              <ul className="mb-4 list-inside list-disc space-y-1 text-gray-700">
                {overview.key_rules.map((rule, i) => (
                  <li key={i}>{rule}</li>
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
