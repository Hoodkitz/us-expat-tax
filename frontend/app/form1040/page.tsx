"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface Form1040Result {
  agi: string;
  taxable_income: string;
  tax_before_credits: string;
  total_tax: string;
  effective_tax_rate: string;
  marginal_tax_rate: string;
  balance_due: string;
  refund: string;
  explanation: string;
}

interface Form1040Overview {
  form: string;
  title: string;
  purpose: string;
  who_must_file: string[];
  key_rules: string[];
  statutory_references: string[];
  irs_reference: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Form1040Page() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Form1040Result | null>(null);
  const [overview, setOverview] = useState<Form1040Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [filingStatus, setFilingStatus] = useState("single");
  const [grossIncome, setGrossIncome] = useState("");
  const [adjustments, setAdjustments] = useState("0");
  const [deductions, setDeductions] = useState("0");
  const [credits, setCredits] = useState("0");
  const [withholding, setWithholding] = useState("0");
  const [taxYear, setTaxYear] = useState(2025);

  useEffect(() => {
    fetchOverview();
  }, []);

  async function fetchOverview() {
    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch(`${API_BASE}/api/v1/form1040/overview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setOverview(data);
      }
    } catch (e) {
      console.error("Failed to fetch overview:", e);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch(`${API_BASE}/api/v1/form1040/calculate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          filing_status: filingStatus,
          gross_income: grossIncome,
          adjustments: adjustments,
          deductions: deductions,
          credits: credits,
          withholding: withholding,
          tax_year: taxYear,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Calculation failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-6">
          <Link href="/" className="text-blue-600 hover:text-blue-800 text-sm">
            ← Back to Dashboard
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Form 1040</h1>
          <p className="text-gray-600 mb-4">U.S. Individual Income Tax Return</p>

          {overview && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h2 className="font-semibold text-blue-900 mb-2">Overview</h2>
              <p className="text-sm text-blue-800 mb-2">{overview.purpose}</p>
              <div className="text-sm text-blue-800">
                <p className="font-medium">Who must file:</p>
                <ul className="list-disc list-inside ml-2">
                  {overview.who_must_file.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Filing Status
                </label>
                <select
                  value={filingStatus}
                  onChange={(e) => setFilingStatus(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
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
                  Tax Year
                </label>
                <input
                  type="number"
                  value={taxYear}
                  onChange={(e) => setTaxYear(parseInt(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gross Income ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={grossIncome}
                  onChange={(e) => setGrossIncome(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Adjustments ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={adjustments}
                  onChange={(e) => setAdjustments(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Deductions ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={deductions}
                  onChange={(e) => setDeductions(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Credits ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={credits}
                  onChange={(e) => setCredits(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Withholding ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={withholding}
                  onChange={(e) => setWithholding(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Calculating..." : "Calculate"}
            </button>
          </form>

          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {result && (
            <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
              <h2 className="font-semibold text-green-900 mb-3">Results</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="font-medium">Adjusted Gross Income:</span> $
                  {parseFloat(result.agi).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Taxable Income:</span> $
                  {parseFloat(result.taxable_income).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Tax Before Credits:</span> $
                  {parseFloat(result.tax_before_credits).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Total Tax:</span> $
                  {parseFloat(result.total_tax).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Effective Tax Rate:</span>{" "}
                  {parseFloat(result.effective_tax_rate).toFixed(2)}%
                </div>
                <div>
                  <span className="font-medium">Marginal Tax Rate:</span>{" "}
                  {parseFloat(result.marginal_tax_rate).toFixed(2)}%
                </div>
                <div>
                  <span className="font-medium">Balance Due:</span> $
                  {parseFloat(result.balance_due).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Refund:</span> $
                  {parseFloat(result.refund).toLocaleString()}
                </div>
              </div>
              <p className="mt-3 text-sm text-green-800">{result.explanation}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
