"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface Schedule2Result {
  total_additional_taxes: string;
  explanation: string;
}

interface Schedule2Overview {
  form: string;
  title: string;
  purpose: string;
  who_must_file: string[];
  key_rules: string[];
  statutory_references: string[];
  irs_reference: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Schedule2Page() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Schedule2Result | null>(null);
  const [overview, setOverview] = useState<Schedule2Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [alternativeMinimumTax, setAlternativeMinimumTax] = useState("0");
  const [excessAdvancePremiumTaxCredit, setExcessAdvancePremiumTaxCredit] = useState("0");
  const [selfEmploymentTax, setSelfEmploymentTax] = useState("0");
  const [additionalMedicareTax, setAdditionalMedicareTax] = useState("0");
  const [netInvestmentIncomeTax, setNetInvestmentIncomeTax] = useState("0");
  const [recaptureTaxes, setRecaptureTaxes] = useState("0");
  const [otherTaxes, setOtherTaxes] = useState("0");
  const [taxYear, setTaxYear] = useState(2025);

  useEffect(() => {
    fetchOverview();
  }, []);

  async function fetchOverview() {
    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch(`${API_BASE}/api/v1/schedule_2/overview`, {
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
      const res = await fetch(`${API_BASE}/api/v1/schedule_2/calculate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          alternative_minimum_tax: alternativeMinimumTax,
          excess_advance_premium_tax_credit: excessAdvancePremiumTaxCredit,
          self_employment_tax: selfEmploymentTax,
          additional_medicare_tax: additionalMedicareTax,
          net_investment_income_tax: netInvestmentIncomeTax,
          recapture_taxes: recaptureTaxes,
          other_taxes: otherTaxes,
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
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Schedule 2</h1>
          <p className="text-gray-600 mb-4">Additional Taxes</p>

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
                  Alternative Minimum Tax ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={alternativeMinimumTax}
                  onChange={(e) => setAlternativeMinimumTax(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Excess Advance Premium Tax Credit ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={excessAdvancePremiumTaxCredit}
                  onChange={(e) => setExcessAdvancePremiumTaxCredit(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Self-Employment Tax ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={selfEmploymentTax}
                  onChange={(e) => setSelfEmploymentTax(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Medicare Tax ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={additionalMedicareTax}
                  onChange={(e) => setAdditionalMedicareTax(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Net Investment Income Tax ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={netInvestmentIncomeTax}
                  onChange={(e) => setNetInvestmentIncomeTax(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Recapture Taxes ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={recaptureTaxes}
                  onChange={(e) => setRecaptureTaxes(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Other Taxes ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={otherTaxes}
                  onChange={(e) => setOtherTaxes(e.target.value)}
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
                  <span className="font-medium">Total Additional Taxes:</span> $
                  {parseFloat(result.total_additional_taxes).toLocaleString()}
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
