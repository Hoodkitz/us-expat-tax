"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiForm8825FilingRequirement,
  apiForm8825IncomeSummary,
  apiForm8825ExpenseCalculation,
  apiForm8825Overview,
  TenantOut,
  FilingRequirement8825Result,
  IncomeSummary8825Result,
  ExpenseCalculation8825Result,
  Form8825Overview,
} from "@/lib/api";

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

type ActiveTab = "filing" | "income-expenses" | "overview";

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
  const [rentalIncome, setRentalIncome] = useState(0);
  const [rentalExpenses, setRentalExpenses] = useState(0);
  const [taxYear, setTaxYear] = useState(new Date().getFullYear() - 1);
  const [filingStatus, setFilingStatus] = useState("single");
  const [participationLevel, setParticipationLevel] = useState("active");
  const [modifiedAgi, setModifiedAgi] = useState(0);
  const [filingResult, setFilingResult] = useState<FilingRequirement8825Result | null>(null);

  // Income Summary State
  const [rentsReceived, setRentsReceived] = useState(0);
  const [advanceRents, setAdvanceRents] = useState(0);
  const [securityDepositsRetained, setSecurityDepositsRetained] = useState(0);
  const [tenantPaidExpenses, setTenantPaidExpenses] = useState(0);
  const [incomeResult, setIncomeResult] = useState<IncomeSummary8825Result | null>(null);

  // Expense Calculation State
  const [advertising, setAdvertising] = useState(0);
  const [autoTravel, setAutoTravel] = useState(0);
  const [cleaningMaintenance, setCleaningMaintenance] = useState(0);
  const [commissions, setCommissions] = useState(0);
  const [insurance, setInsurance] = useState(0);
  const [legalProfessionalFees, setLegalProfessionalFees] = useState(0);
  const [managementFees, setManagementFees] = useState(0);
  const [mortgageInterest, setMortgageInterest] = useState(0);
  const [repairs, setRepairs] = useState(0);
  const [supplies, setSupplies] = useState(0);
  const [taxes, setTaxes] = useState(0);
  const [utilities, setUtilities] = useState(0);
  const [depreciation, setDepreciation] = useState(0);
  const [otherExpenses, setOtherExpenses] = useState(0);
  const [expenseResult, setExpenseResult] = useState<ExpenseCalculation8825Result | null>(null);

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
        rental_income: rentalIncome,
        rental_expenses: rentalExpenses,
        tax_year: taxYear,
        filing_status: filingStatus as any,
        participation_level: participationLevel as any,
        modified_agi: modifiedAgi,
      });
      setFilingResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const calculateIncomeSummary = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiForm8825IncomeSummary({
        rents_received: rentsReceived,
        advance_rents: advanceRents,
        security_deposits_retained: securityDepositsRetained,
        rental_expenses_paid_by_tenant: tenantPaidExpenses,
        tax_year: taxYear,
      });
      setIncomeResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const calculateExpenses = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiForm8825ExpenseCalculation({
        advertising,
        auto_travel: autoTravel,
        cleaning_maintenance: cleaningMaintenance,
        commissions,
        insurance,
        legal_professional_fees: legalProfessionalFees,
        management_fees: managementFees,
        mortgage_interest: mortgageInterest,
        repairs,
        supplies,
        taxes,
        utilities,
        depreciation,
        other_expenses: otherExpenses,
        tax_year: taxYear,
      });
      setExpenseResult(data);
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
              Form 8825: Rental Real Estate
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
            onClick={() => setActiveTab("income-expenses")}
            className={`px-4 py-2 font-medium text-sm rounded-t-lg ${
              activeTab === "income-expenses"
                ? "bg-white text-blue-600 border border-b-white"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Income & Expenses
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
                    <option value="trust">Trust</option>
                    <option value="estate">Estate</option>
                    <option value="partnership">Partnership</option>
                    <option value="corporation">Corporation</option>
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
                    Rental Income ($)
                  </label>
                  <input
                    type="number"
                    value={rentalIncome}
                    onChange={(e) => setRentalIncome(Number(e.target.value))}
                    min={0}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rental Expenses ($)
                  </label>
                  <input
                    type="number"
                    value={rentalExpenses}
                    onChange={(e) => setRentalExpenses(Number(e.target.value))}
                    min={0}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Filing Status
                  </label>
                  <select
                    value={filingStatus}
                    onChange={(e) => setFilingStatus(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="single">Single</option>
                    <option value="married_filing_jointly">Married Filing Jointly</option>
                    <option value="married_filing_separately">Married Filing Separately</option>
                    <option value="head_of_household">Head of Household</option>
                    <option value="qualifying_widow">Qualifying Widow(er)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Participation Level
                  </label>
                  <select
                    value={participationLevel}
                    onChange={(e) => setParticipationLevel(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="active">Active Participant</option>
                    <option value="passive">Passive Participant</option>
                    <option value="real_estate_professional">Real Estate Professional</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Modified AGI ($)
                  </label>
                  <input
                    type="number"
                    value={modifiedAgi}
                    onChange={(e) => setModifiedAgi(Number(e.target.value))}
                    min={0}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
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

                  <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                    <div>
                      <p className="text-sm text-gray-600">Net Rental Income</p>
                      <p className="text-lg font-semibold">{fmtUSD(filingResult.net_rental_income)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Passive Loss Limit</p>
                      <p className="text-lg font-semibold">{fmtUSD(filingResult.passive_loss_limit)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Allowed Passive Loss</p>
                      <p className="text-lg font-semibold text-green-600">{fmtUSD(filingResult.allowed_passive_loss)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Suspended Passive Loss</p>
                      <p className="text-lg font-semibold text-red-600">{fmtUSD(filingResult.suspended_passive_loss)}</p>
                    </div>
                  </div>

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
                </div>
              ) : (
                <p className="text-gray-500 text-sm">
                  Fill out the form and click &quot;Check Filing Requirement&quot; to see if Form 8825 is required.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Income & Expenses Tab */}
        {activeTab === "income-expenses" && (
          <div className="space-y-8">
            {/* Income Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h2 className="text-lg font-semibold mb-4">Rental Income Summary</h2>

                <div className="space-y-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Rents Received ($)
                    </label>
                    <input
                      type="number"
                      value={rentsReceived}
                      onChange={(e) => setRentsReceived(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Advance Rents ($)
                    </label>
                    <input
                      type="number"
                      value={advanceRents}
                      onChange={(e) => setAdvanceRents(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Security Deposits Retained ($)
                    </label>
                    <input
                      type="number"
                      value={securityDepositsRetained}
                      onChange={(e) => setSecurityDepositsRetained(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Expenses Paid by Tenant ($)
                    </label>
                    <input
                      type="number"
                      value={tenantPaidExpenses}
                      onChange={(e) => setTenantPaidExpenses(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <button
                  onClick={calculateIncomeSummary}
                  disabled={loading}
                  className="w-full py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "Calculating..." : "Calculate Income Summary"}
                </button>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h2 className="text-lg font-semibold mb-4">Income Result</h2>
                {incomeResult ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm mb-2">
                        <strong>Gross Rental Income:</strong> {fmtUSD(incomeResult.gross_rental_income)}
                      </p>
                      <p className="text-sm mb-2">
                        <strong>Advance Rents:</strong> {fmtUSD(incomeResult.advance_rents)}
                      </p>
                      <p className="text-sm mb-2">
                        <strong>Security Deposits Retained:</strong> {fmtUSD(incomeResult.security_deposits_retained)}
                      </p>
                      <p className="text-sm mb-2">
                        <strong>Tenant-Paid Expenses:</strong> {fmtUSD(incomeResult.tenant_paid_expenses)}
                      </p>
                      <p className="text-lg font-bold mt-3">
                        <strong>Total Rental Income:</strong> {fmtUSD(incomeResult.total_rental_income)}
                      </p>
                    </div>
                    <pre className="text-xs text-gray-600 whitespace-pre-wrap">{incomeResult.explanation}</pre>
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">
                    Fill out the form and click &quot;Calculate Income Summary&quot; to see your total rental income.
                  </p>
                )}
              </div>
            </div>

            {/* Expense Calculation */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h2 className="text-lg font-semibold mb-4">Rental Expenses</h2>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Advertising</label>
                    <input
                      type="number"
                      value={advertising}
                      onChange={(e) => setAdvertising(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Auto & Travel</label>
                    <input
                      type="number"
                      value={autoTravel}
                      onChange={(e) => setAutoTravel(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Cleaning & Maintenance</label>
                    <input
                      type="number"
                      value={cleaningMaintenance}
                      onChange={(e) => setCleaningMaintenance(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Commissions</label>
                    <input
                      type="number"
                      value={commissions}
                      onChange={(e) => setCommissions(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Insurance</label>
                    <input
                      type="number"
                      value={insurance}
                      onChange={(e) => setInsurance(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Legal & Professional Fees</label>
                    <input
                      type="number"
                      value={legalProfessionalFees}
                      onChange={(e) => setLegalProfessionalFees(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Management Fees</label>
                    <input
                      type="number"
                      value={managementFees}
                      onChange={(e) => setManagementFees(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mortgage Interest</label>
                    <input
                      type="number"
                      value={mortgageInterest}
                      onChange={(e) => setMortgageInterest(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Repairs</label>
                    <input
                      type="number"
                      value={repairs}
                      onChange={(e) => setRepairs(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Supplies</label>
                    <input
                      type="number"
                      value={supplies}
                      onChange={(e) => setSupplies(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Property Taxes</label>
                    <input
                      type="number"
                      value={taxes}
                      onChange={(e) => setTaxes(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Utilities</label>
                    <input
                      type="number"
                      value={utilities}
                      onChange={(e) => setUtilities(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Depreciation</label>
                    <input
                      type="number"
                      value={depreciation}
                      onChange={(e) => setDepreciation(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Other Expenses</label>
                    <input
                      type="number"
                      value={otherExpenses}
                      onChange={(e) => setOtherExpenses(Number(e.target.value))}
                      min={0}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <button
                  onClick={calculateExpenses}
                  disabled={loading}
                  className="w-full py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "Calculating..." : "Calculate Expenses"}
                </button>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h2 className="text-lg font-semibold mb-4">Expense Result</h2>
                {expenseResult ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm mb-2">
                        <strong>Total Expenses:</strong> {fmtUSD(expenseResult.total_expenses)}
                      </p>
                      <p className="text-sm mb-2">
                        <strong>Deductible Expenses:</strong> {fmtUSD(expenseResult.deductible_expenses)}
                      </p>
                      <p className="text-sm mb-2">
                        <strong>Non-Deductible Expenses:</strong> {fmtUSD(expenseResult.non_deductible_expenses)}
                      </p>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Expense Breakdown</h3>
                      <div className="space-y-1">
                        {Object.entries(expenseResult.expense_breakdown)
                          .filter(([, amount]) => amount > 0)
                          .map(([category, amount]) => (
                            <div key={category} className="flex justify-between text-sm">
                              <span className="text-gray-600">
                                {category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                              </span>
                              <span className="font-medium">{fmtUSD(amount)}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">
                    Fill out the form and click &quot;Calculate Expenses&quot; to see your total rental expenses.
                  </p>
                )}
              </div>
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
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="font-medium text-green-900 mb-2">Income Types</h3>
                <ul className="list-disc list-inside text-sm text-green-800 space-y-1">
                  {overview.income_types.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Expense Categories</h3>
                <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
                  {overview.expense_categories.slice(0, 7).map((item, i) => (
                    <li key={i}>{item.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-2">Passive Loss Rules</h3>
              <p className="text-sm text-gray-700">{overview.passive_loss_rules}</p>
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
