"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiMe, TenantOut } from "@/lib/api";

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

interface FilingRequirementResult {
  filing_required: boolean;
  reasons: string[];
  recommendation: string;
  total_us_income: number;
  tax_withheld: number;
  estimated_tax_due: number;
}

interface TaxCalculationResult {
  tax_year: number;
  filing_status: string;
  total_income: number;
  adjusted_gross_income: number;
  total_deductions: number;
  taxable_income: number;
  tax_before_credits: number;
  total_credits: number;
  tax_after_credits: number;
  federal_tax_withheld: number;
  tax_due: number;
  refund: number;
  effective_tax_rate: number;
  marginal_tax_rate: number;
  income_breakdown: Record<string, number>;
  tax_bracket_breakdown: Array<{
    bracket_lower: number;
    bracket_upper: number | null;
    rate: number;
    taxable_amount: number;
    tax_amount: number;
  }>;
  treaty_applied: boolean;
  treaty_rate: number | null;
}

interface OverviewData {
  form_name: string;
  form_title: string;
  description: string;
  filing_deadline: string;
  who_must_file: string[];
  income_types: string[];
  tax_rates: Record<string, string>;
  deductions_available: string[];
  credits_available: string[];
  special_rules: string[];
}

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function fmtUSD(val: number | undefined): string {
  if (val === undefined || val === null) return "–";
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(val);
}

function fmtPct(val: number | null | undefined): string {
  if (val === undefined || val === null) return "–";
  return `${(val * 100).toFixed(1)}%`;
}

// -----------------------------------------------------------------------
// Main Page Component
// -----------------------------------------------------------------------

export default function Form1040NRPage() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [authError, setAuthError] = useState(false);
  const [activeTab, setActiveTab] = useState<"filing" | "calculate" | "overview">("filing");

  // Overview state
  const [overview, setOverview] = useState<OverviewData | null>(null);

  // Filing requirement state
  const [filingTaxYear, setFilingTaxYear] = useState(2024);
  const [usSourceIncome, setUsSourceIncome] = useState(0);
  const [eciIncome, setEciIncome] = useState(0);
  const [fdapIncome, setFdapIncome] = useState(0);
  const [taxWithheld, setTaxWithheld] = useState(0);
  const [isTreatyResident, setIsTreatyResident] = useState(false);
  const [treatyRate, setTreatyRate] = useState<number | undefined>(undefined);
  const [filingResult, setFilingResult] = useState<FilingRequirementResult | null>(null);

  // Tax calculation state
  const [calcTaxYear, setCalcTaxYear] = useState(2024);
  const [filingStatus, setFilingStatus] = useState("Single");
  const [wages, setWages] = useState(0);
  const [interestIncome, setInterestIncome] = useState(0);
  const [dividendIncome, setDividendIncome] = useState(0);
  const [capitalGains, setCapitalGains] = useState(0);
  const [businessIncome, setBusinessIncome] = useState(0);
  const [rentalIncome, setRentalIncome] = useState(0);
  const [otherIncome, setOtherIncome] = useState(0);
  const [itemizedDeductions, setItemizedDeductions] = useState(0);
  const [studentLoanInterest, setStudentLoanInterest] = useState(0);
  const [iraDeduction, setIraDeduction] = useState(0);
  const [foreignTaxCredit, setForeignTaxCredit] = useState(0);
  const [childTaxCredit, setChildTaxCredit] = useState(0);
  const [otherCredits, setOtherCredits] = useState(0);
  const [federalTaxWithheld, setFederalTaxWithheld] = useState(0);
  const [calcTreatyResident, setCalcTreatyResident] = useState(false);
  const [calcTreatyRate, setCalcTreatyRate] = useState<number | undefined>(undefined);
  const [calcResult, setCalcResult] = useState<TaxCalculationResult | null>(null);

  // UI state
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

  // ---- Load overview ----
  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) return;
    fetch("/api/v1/form1040nr/overview", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => setOverview(data))
      .catch(() => {});
  }, []);

  // ---- Filing Check Handler ----
  const handleFilingCheck = async () => {
    setLoading(true);
    setError(null);
    setFilingResult(null);
    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch("/api/v1/form1040nr/filing-requirement", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          tax_year: filingTaxYear,
          us_source_income: usSourceIncome,
          effectively_connected_income: eciIncome,
          fdap_income: fdapIncome,
          tax_withheld: taxWithheld,
          is_treaty_country_resident: isTreatyResident,
          treaty_reduced_rate: treatyRate,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Fehler");
      setFilingResult(data);
    } catch (err: any) {
      setError(err.message || "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  };

  // ---- Tax Calculation Handler ----
  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    setCalcResult(null);
    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch("/api/v1/form1040nr/calculate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          tax_year: calcTaxYear,
          filing_status: filingStatus,
          wages_salaries: wages,
          interest_income: interestIncome,
          dividend_income: dividendIncome,
          capital_gains: capitalGains,
          business_income: businessIncome,
          rental_income: rentalIncome,
          other_income: otherIncome,
          itemized_deductions: itemizedDeductions,
          student_loan_interest: studentLoanInterest,
          ira_deduction: iraDeduction,
          foreign_tax_credit: foreignTaxCredit,
          child_tax_credit: childTaxCredit,
          other_credits: otherCredits,
          federal_tax_withheld: federalTaxWithheld,
          is_treaty_country_resident: calcTreatyResident,
          treaty_reduced_rate: calcTreatyRate,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Fehler");
      setCalcResult(data);
    } catch (err: any) {
      setError(err.message || "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  };

  if (authError) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="text-4xl">📄</div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">Form 1040-NR</h1>
                <p className="text-slate-600">U.S. Nonresident Alien Income Tax Return</p>
              </div>
            </div>
            <Link href="/" className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition">
              ← Dashboard
            </Link>
          </div>
          {overview && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-slate-700">{overview.description}</p>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-lg mb-6">
          <div className="flex border-b border-slate-200">
            <button
              onClick={() => setActiveTab("filing")}
              className={`flex-1 py-4 px-6 text-center font-semibold transition ${
                activeTab === "filing"
                  ? "bg-blue-600 text-white rounded-t-xl"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Filing Check
            </button>
            <button
              onClick={() => setActiveTab("calculate")}
              className={`flex-1 py-4 px-6 text-center font-semibold transition ${
                activeTab === "calculate"
                  ? "bg-blue-600 text-white rounded-t-xl"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Tax Calculation
            </button>
            <button
              onClick={() => setActiveTab("overview")}
              className={`flex-1 py-4 px-6 text-center font-semibold transition ${
                activeTab === "overview"
                  ? "bg-blue-600 text-white rounded-t-xl"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Overview
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* ---- Filing Check Tab ---- */}
            {activeTab === "filing" && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-slate-900">Filing Requirement Check</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Tax Year</label>
                    <input
                      type="number"
                      value={filingTaxYear}
                      onChange={(e) => setFilingTaxYear(Number(e.target.value))}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">US Source Income (USD)</label>
                    <input
                      type="number"
                      value={usSourceIncome}
                      onChange={(e) => setUsSourceIncome(Number(e.target.value))}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      min="0"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Effectively Connected Income (USD)</label>
                    <input
                      type="number"
                      value={eciIncome}
                      onChange={(e) => setEciIncome(Number(e.target.value))}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      min="0"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">FDAP Income (USD)</label>
                    <input
                      type="number"
                      value={fdapIncome}
                      onChange={(e) => setFdapIncome(Number(e.target.value))}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      min="0"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Tax Withheld (USD)</label>
                    <input
                      type="number"
                      value={taxWithheld}
                      onChange={(e) => setTaxWithheld(Number(e.target.value))}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      min="0"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={isTreatyResident}
                      onChange={(e) => setIsTreatyResident(e.target.checked)}
                      className="h-5 w-5"
                    />
                    <label className="text-sm font-medium text-slate-700">Treaty Country Resident</label>
                  </div>
                  {isTreatyResident && (
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Treaty Rate (optional)</label>
                      <input
                        type="number"
                        value={treatyRate || ""}
                        onChange={(e) => setTreatyRate(e.target.value ? Number(e.target.value) : undefined)}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                        max="1"
                        step="0.01"
                        placeholder="z.B. 0.15 für 15%"
                      />
                    </div>
                  )}
                </div>

                <button
                  onClick={handleFilingCheck}
                  disabled={loading}
                  className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-slate-400"
                >
                  {loading ? "Calculating..." : "Check Filing Requirement"}
                </button>

                {error && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-800 font-semibold">Error:</p>
                    <p className="text-red-700">{error}</p>
                  </div>
                )}

                {filingResult && (
                  <div className="p-6 bg-white border-2 border-blue-200 rounded-lg">
                    <h3 className="text-xl font-bold text-slate-900 mb-4">Filing Requirement Result</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-slate-600">Filing Required</p>
                        <p className={`text-2xl font-bold ${filingResult.filing_required ? "text-red-600" : "text-green-600"}`}>
                          {filingResult.filing_required ? "YES" : "NO"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Total US Income</p>
                        <p className="text-lg font-semibold text-slate-900">{fmtUSD(filingResult.total_us_income)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Tax Withheld</p>
                        <p className="text-lg font-semibold text-slate-900">{fmtUSD(filingResult.tax_withheld)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Estimated Tax Due</p>
                        <p className="text-lg font-semibold text-red-600">{fmtUSD(filingResult.estimated_tax_due)}</p>
                      </div>
                    </div>
                    <div className="mb-4">
                      <p className="text-sm font-semibold text-slate-700 mb-2">Reasons:</p>
                      <ul className="list-disc list-inside space-y-1">
                        {filingResult.reasons.map((r, i) => (
                          <li key={i} className="text-sm text-slate-700">{r}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm font-semibold text-slate-700 mb-1">Recommendation:</p>
                      <p className="text-sm text-slate-700">{filingResult.recommendation}</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ---- Tax Calculation Tab ---- */}
            {activeTab === "calculate" && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-slate-900">Tax Calculation</h2>

                {/* Filing Status */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Tax Year</label>
                    <input
                      type="number"
                      value={calcTaxYear}
                      onChange={(e) => setCalcTaxYear(Number(e.target.value))}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Filing Status</label>
                    <select
                      value={filingStatus}
                      onChange={(e) => setFilingStatus(e.target.value)}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    >
                      <option value="Single">Single</option>
                      <option value="Married Filing Jointly">Married Filing Jointly</option>
                    </select>
                  </div>
                </div>

                {/* Income Section */}
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-3">Income</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Wages, Salaries (USD)</label>
                      <input
                        type="number"
                        value={wages}
                        onChange={(e) => setWages(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Interest Income (USD)</label>
                      <input
                        type="number"
                        value={interestIncome}
                        onChange={(e) => setInterestIncome(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Dividend Income (USD)</label>
                      <input
                        type="number"
                        value={dividendIncome}
                        onChange={(e) => setDividendIncome(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Capital Gains (USD)</label>
                      <input
                        type="number"
                        value={capitalGains}
                        onChange={(e) => setCapitalGains(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Business Income (USD)</label>
                      <input
                        type="number"
                        value={businessIncome}
                        onChange={(e) => setBusinessIncome(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Rental Income (USD)</label>
                      <input
                        type="number"
                        value={rentalIncome}
                        onChange={(e) => setRentalIncome(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Other Income (USD)</label>
                      <input
                        type="number"
                        value={otherIncome}
                        onChange={(e) => setOtherIncome(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                  </div>
                </div>

                {/* Deductions Section */}
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-3">Deductions</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Itemized Deductions (USD)</label>
                      <input
                        type="number"
                        value={itemizedDeductions}
                        onChange={(e) => setItemizedDeductions(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Student Loan Interest (USD)</label>
                      <input
                        type="number"
                        value={studentLoanInterest}
                        onChange={(e) => setStudentLoanInterest(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">IRA Deduction (USD)</label>
                      <input
                        type="number"
                        value={iraDeduction}
                        onChange={(e) => setIraDeduction(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                  </div>
                </div>

                {/* Credits Section */}
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-3">Tax Credits</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Foreign Tax Credit (USD)</label>
                      <input
                        type="number"
                        value={foreignTaxCredit}
                        onChange={(e) => setForeignTaxCredit(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Child Tax Credit (USD)</label>
                      <input
                        type="number"
                        value={childTaxCredit}
                        onChange={(e) => setChildTaxCredit(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Other Credits (USD)</label>
                      <input
                        type="number"
                        value={otherCredits}
                        onChange={(e) => setOtherCredits(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                  </div>
                </div>

                {/* Withholding & Treaty */}
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-3">Withholding & Treaty</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Federal Tax Withheld (USD)</label>
                      <input
                        type="number"
                        value={federalTaxWithheld}
                        onChange={(e) => setFederalTaxWithheld(Number(e.target.value))}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        min="0"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={calcTreatyResident}
                        onChange={(e) => setCalcTreatyResident(e.target.checked)}
                        className="h-5 w-5"
                      />
                      <label className="text-sm font-medium text-slate-700">Treaty Country Resident</label>
                    </div>
                    {calcTreatyResident && (
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Treaty Rate (optional)</label>
                        <input
                          type="number"
                          value={calcTreatyRate || ""}
                          onChange={(e) => setCalcTreatyRate(e.target.value ? Number(e.target.value) : undefined)}
                          className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                          min="0"
                          max="1"
                          step="0.01"
                          placeholder="z.B. 0.15 für 15%"
                        />
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={handleCalculate}
                  disabled={loading}
                  className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-slate-400"
                >
                  {loading ? "Calculating..." : "Calculate Tax"}
                </button>

                {error && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-800 font-semibold">Error:</p>
                    <p className="text-red-700">{error}</p>
                  </div>
                )}

                {calcResult && (
                  <div className="p-6 bg-white border-2 border-blue-200 rounded-lg space-y-6">
                    <h3 className="text-xl font-bold text-slate-900">Tax Calculation Result</h3>

                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-4 bg-slate-50 rounded-lg">
                        <p className="text-sm text-slate-600">Total Income</p>
                        <p className="text-2xl font-bold text-slate-900">{fmtUSD(calcResult.total_income)}</p>
                      </div>
                      <div className="p-4 bg-slate-50 rounded-lg">
                        <p className="text-sm text-slate-600">Taxable Income</p>
                        <p className="text-2xl font-bold text-slate-900">{fmtUSD(calcResult.taxable_income)}</p>
                      </div>
                      <div className="p-4 bg-slate-50 rounded-lg">
                        <p className="text-sm text-slate-600">Effective Tax Rate</p>
                        <p className="text-2xl font-bold text-slate-900">{calcResult.effective_tax_rate.toFixed(1)}%</p>
                      </div>
                    </div>

                    {/* Tax Breakdown */}
                    <div>
                      <h4 className="text-lg font-semibold text-slate-900 mb-3">Tax Breakdown</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between py-2 border-b border-slate-200">
                          <span className="text-slate-600">Tax Before Credits</span>
                          <span className="font-semibold text-slate-900">{fmtUSD(calcResult.tax_before_credits)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-slate-200">
                          <span className="text-slate-600">Total Credits</span>
                          <span className="font-semibold text-green-600">-{fmtUSD(calcResult.total_credits)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-slate-200">
                          <span className="text-slate-600">Tax After Credits</span>
                          <span className="font-semibold text-slate-900">{fmtUSD(calcResult.tax_after_credits)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-slate-200">
                          <span className="text-slate-600">Federal Tax Withheld</span>
                          <span className="font-semibold text-slate-900">{fmtUSD(calcResult.federal_tax_withheld)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-b border-slate-200">
                          <span className="text-slate-600">Marginal Tax Rate</span>
                          <span className="font-semibold text-slate-900">{fmtPct(calcResult.marginal_tax_rate)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Result */}
                    <div className={`p-4 rounded-lg ${calcResult.tax_due > 0 ? "bg-red-50 border border-red-200" : "bg-green-50 border border-green-200"}`}>
                      <div className="flex justify-between items-center">
                        <span className="text-lg font-semibold text-slate-900">
                          {calcResult.tax_due > 0 ? "Tax Due" : "Refund"}
                        </span>
                        <span className={`text-2xl font-bold ${calcResult.tax_due > 0 ? "text-red-600" : "text-green-600"}`}>
                          {fmtUSD(calcResult.tax_due > 0 ? calcResult.tax_due : calcResult.refund)}
                        </span>
                      </div>
                    </div>

                    {/* Income Breakdown */}
                    <div>
                      <h4 className="text-lg font-semibold text-slate-900 mb-3">Income Breakdown</h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {Object.entries(calcResult.income_breakdown).map(([key, value]) => (
                          <div key={key} className="p-2 bg-slate-50 rounded">
                            <p className="text-xs text-slate-500 capitalize">{key.replace(/_/g, " ")}</p>
                            <p className="text-sm font-semibold text-slate-900">{fmtUSD(value)}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Tax Bracket Breakdown */}
                    {calcResult.tax_bracket_breakdown.length > 0 && (
                      <div>
                        <h4 className="text-lg font-semibold text-slate-900 mb-3">Tax Bracket Breakdown</h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-slate-200">
                                <th className="text-left py-2 text-slate-600">Bracket</th>
                                <th className="text-right py-2 text-slate-600">Rate</th>
                                <th className="text-right py-2 text-slate-600">Taxable Amount</th>
                                <th className="text-right py-2 text-slate-600">Tax</th>
                              </tr>
                            </thead>
                            <tbody>
                              {calcResult.tax_bracket_breakdown.map((bracket, i) => (
                                <tr key={i} className="border-b border-slate-100">
                                  <td className="py-2 text-slate-900">
                                    {fmtUSD(bracket.bracket_lower)} - {bracket.bracket_upper ? fmtUSD(bracket.bracket_upper) : "∞"}
                                  </td>
                                  <td className="py-2 text-right text-slate-900">{fmtPct(bracket.rate)}</td>
                                  <td className="py-2 text-right text-slate-900">{fmtUSD(bracket.taxable_amount)}</td>
                                  <td className="py-2 text-right text-slate-900">{fmtUSD(bracket.tax_amount)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Treaty Info */}
                    {calcResult.treaty_applied && (
                      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="text-sm font-semibold text-blue-800">Treaty Applied</p>
                        <p className="text-sm text-blue-700">Reduced rate: {fmtPct(calcResult.treaty_rate)}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ---- Overview Tab ---- */}
            {activeTab === "overview" && overview && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-slate-900">Form 1040-NR Overview</h2>

                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-slate-700">{overview.description}</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Filing Deadline</h3>
                  <p className="text-slate-700">{overview.filing_deadline}</p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Who Must File</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {overview.who_must_file.map((item, i) => (
                      <li key={i} className="text-sm text-slate-700">{item}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Income Types</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {overview.income_types.map((item, i) => (
                      <li key={i} className="text-sm text-slate-700">{item}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Tax Rates</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(overview.tax_rates).map(([key, value]) => (
                      <div key={key} className="p-3 bg-slate-50 rounded-lg">
                        <p className="text-sm font-semibold text-slate-900">{key}</p>
                        <p className="text-sm text-slate-600">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Deductions Available</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {overview.deductions_available.map((item, i) => (
                      <li key={i} className="text-sm text-slate-700">{item}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Credits Available</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {overview.credits_available.map((item, i) => (
                      <li key={i} className="text-sm text-slate-700">{item}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Special Rules</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {overview.special_rules.map((item, i) => (
                      <li key={i} className="text-sm text-slate-700">{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
