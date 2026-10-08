"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface Form4562Result {
  section_179_deduction: string;
  bonus_depreciation: string;
  regular_depreciation: string;
  total_depreciation: string;
  explanation: string;
}

interface Form4562Overview {
  form: string;
  title: string;
  purpose: string;
  who_must_file: string[];
  key_rules: string[];
  statutory_references: string[];
  irs_reference: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Form4562Page() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Form4562Result | null>(null);
  const [overview, setOverview] = useState<Form4562Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [assetCost, setAssetCost] = useState("");
  const [assetType, setAssetType] = useState("5");
  const [businessUsePercentage, setBusinessUsePercentage] = useState("100");
  const [section179Election, setSection179Election] = useState("0");
  const [bonusDepreciation, setBonusDepreciation] = useState("0");
  const [taxYear, setTaxYear] = useState(2025);

  useEffect(() => {
    fetchOverview();
  }, []);

  async function fetchOverview() {
    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch(`${API_BASE}/api/v1/form4562/overview`, {
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
      const res = await fetch(`${API_BASE}/api/v1/form4562/calculate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          asset_cost: assetCost,
          asset_type: assetType,
          business_use_percentage: businessUsePercentage,
          section_179_election: section179Election,
          bonus_depreciation: bonusDepreciation,
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
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Form 4562</h1>
          <p className="text-gray-600 mb-4">Depreciation and Amortization</p>

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
                  Asset Cost ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={assetCost}
                  onChange={(e) => setAssetCost(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Asset Type (Recovery Period)
                </label>
                <select
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="5">5-Year Property</option>
                  <option value="7">7-Year Property</option>
                  <option value="15">15-Year Property</option>
                  <option value="27.5">27.5-Year Residential Rental</option>
                  <option value="39">39-Year Nonresidential Real Property</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Business Use Percentage (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={businessUsePercentage}
                  onChange={(e) => setBusinessUsePercentage(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Section 179 Election ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={section179Election}
                  onChange={(e) => setSection179Election(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bonus Depreciation ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={bonusDepreciation}
                  onChange={(e) => setBonusDepreciation(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
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
                  <span className="font-medium">Section 179 Deduction:</span> $
                  {parseFloat(result.section_179_deduction).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Bonus Depreciation:</span> $
                  {parseFloat(result.bonus_depreciation).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Regular Depreciation:</span> $
                  {parseFloat(result.regular_depreciation).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Total Depreciation:</span> $
                  {parseFloat(result.total_depreciation).toLocaleString()}
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
