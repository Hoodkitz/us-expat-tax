"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface Schedule1Result {
  total_additional_income: string;
  total_adjustments: string;
  net_adjustment: string;
  explanation: string;
}

interface Schedule1Overview {
  form: string;
  title: string;
  purpose: string;
  who_must_file: string[];
  key_rules: string[];
  statutory_references: string[];
  irs_reference: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Schedule1Page() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Schedule1Result | null>(null);
  const [overview, setOverview] = useState<Schedule1Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [alimonyReceived, setAlimonyReceived] = useState("0");
  const [businessIncome, setBusinessIncome] = useState("0");
  const [otherGains, setOtherGains] = useState("0");
  const [rentalIncome, setRentalIncome] = useState("0");
  const [farmIncome, setFarmIncome] = useState("0");
  const [unemploymentCompensation, setUnemploymentCompensation] = useState("0");
  const [otherIncome, setOtherIncome] = useState("0");
  const [educatorExpenses, setEducatorExpenses] = useState("0");
  const [hsaDeduction, setHsaDeduction] = useState("0");
  const [studentLoanInterest, setStudentLoanInterest] = useState("0");
  const [iraDeduction, setIraDeduction] = useState("0");
  const [selfEmploymentTaxDeduction, setSelfEmploymentTaxDeduction] = useState("0");
  const [taxYear, setTaxYear] = useState(2025);

  useEffect(() => {
    fetchOverview();
  }, []);

  async function fetchOverview() {
    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch(`${API_BASE}/api/v1/schedule_1/overview`, {
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
      const res = await fetch(`${API_BASE}/api/v1/schedule_1/calculate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          alimony_received: alimonyReceived,
          business_income: businessIncome,
          other_gains: otherGains,
          rental_income: rentalIncome,
          farm_income: farmIncome,
          unemployment_compensation: unemploymentCompensation,
          other_income: otherIncome,
          educator_expenses: educatorExpenses,
          hsa_deduction: hsaDeduction,
          student_loan_interest: studentLoanInterest,
          ira_deduction: iraDeduction,
          self_employment_tax_deduction: selfEmploymentTaxDeduction,
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
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Schedule 1</h1>
          <p className="text-gray-600 mb-4">Additional Income and Adjustments to Income</p>

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
                  Alimony Received ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={alimonyReceived}
                  onChange={(e) => setAlimonyReceived(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Business Income ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={businessIncome}
                  onChange={(e) => setBusinessIncome(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Other Gains ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={otherGains}
                  onChange={(e) => setOtherGains(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rental Income ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={rentalIncome}
                  onChange={(e) => setRentalIncome(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Farm Income ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={farmIncome}
                  onChange={(e) => setFarmIncome(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Unemployment Compensation ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={unemploymentCompensation}
                  onChange={(e) => setUnemploymentCompensation(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Other Income ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={otherIncome}
                  onChange={(e) => setOtherIncome(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Educator Expenses ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={educatorExpenses}
                  onChange={(e) => setEducatorExpenses(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  HSA Deduction ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={hsaDeduction}
                  onChange={(e) => setHsaDeduction(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Student Loan Interest ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={studentLoanInterest}
                  onChange={(e) => setStudentLoanInterest(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  IRA Deduction ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={iraDeduction}
                  onChange={(e) => setIraDeduction(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Self-Employment Tax Deduction ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={selfEmploymentTaxDeduction}
                  onChange={(e) => setSelfEmploymentTaxDeduction(e.target.value)}
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
                  <span className="font-medium">Total Additional Income:</span> $
                  {parseFloat(result.total_additional_income).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Total Adjustments:</span> $
                  {parseFloat(result.total_adjustments).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Net Adjustment:</span> $
                  {parseFloat(result.net_adjustment).toLocaleString()}
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
