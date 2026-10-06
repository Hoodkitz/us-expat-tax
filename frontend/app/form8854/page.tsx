"use client";

import { useState } from "react";

interface FilingRequirementResult {
  covered_expatriate: boolean;
  net_worth_test: {
    exceeds_threshold: boolean;
    net_worth: number;
    threshold: number;
  };
  tax_liability_test: {
    exceeds_threshold: boolean;
    five_year_avg_tax: number;
    threshold: number;
  };
  long_term_resident_test: {
    is_long_term_resident: boolean;
    years_of_residence: number;
    required_years: number;
  };
}

interface ExitTaxResult {
  fair_market_value: number;
  adjusted_basis: number;
  unrealized_gain: number;
  exemption: number;
  exemption_used: number;
  taxable_gain: number;
  capital_gains_rate: number;
  exit_tax: number;
}

interface PenaltyResult {
  total_penalties: number;
  penalties: Array<{
    months_late: number;
    penalty_per_occurrence: number;
    total_penalty: number;
    description: string;
  }>;
}

interface Overview {
  form_name: string;
  description: string;
  purpose: string;
  covered_expatriate_tests: {
    net_worth_threshold: number;
    tax_liability_threshold_2025: number;
    long_term_resident_requirement: string;
  };
  exit_tax: {
    mark_to_market_exemption_2025: number;
    typical_capital_gains_rate: number;
  };
  penalties: {
    failure_to_file: number;
  };
  filing_requirement: string;
  due_date: string;
}

export default function Form8854Page() {
  const [activeTab, setActiveTab] = useState<
    "filing" | "exit-tax" | "penalty" | "overview"
  >("filing");

  // Filing Requirement State
  const [netWorth, setNetWorth] = useState("");
  const [fiveYearAvgTax, setFiveYearAvgTax] = useState("");
  const [yearsOfResidence, setYearsOfResidence] = useState("");
  const [filingResult, setFilingResult] =
    useState<FilingRequirementResult | null>(null);

  // Exit Tax State
  const [fmv, setFmv] = useState("");
  const [adjustedBasis, setAdjustedBasis] = useState("");
  const [capitalGainsRate, setCapitalGainsRate] = useState("0.20");
  const [exitTaxResult, setExitTaxResult] = useState<ExitTaxResult | null>(
    null
  );

  // Penalty State
  const [failedToFile, setFailedToFile] = useState(false);
  const [monthsLate, setMonthsLate] = useState("");
  const [penaltyResult, setPenaltyResult] = useState<PenaltyResult | null>(
    null
  );

  // Overview State
  const [overview, setOverview] = useState<Overview | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const getAuthHeaders = () => {
    const token = localStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const handleFilingRequirement = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/form8854/filing-requirement",
        {
          method: "POST",
          headers: getAuthHeaders(),
          body: JSON.stringify({
            net_worth: parseFloat(netWorth),
            five_year_avg_tax: parseFloat(fiveYearAvgTax),
            years_of_residence: parseInt(yearsOfResidence),
            year: 2025,
          }),
        }
      );
      if (!response.ok) throw new Error("Failed to calculate filing requirement");
      const data = await response.json();
      setFilingResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExitTaxCalculation = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/form8854/exit-tax-calculation",
        {
          method: "POST",
          headers: getAuthHeaders(),
          body: JSON.stringify({
            fair_market_value: parseFloat(fmv),
            adjusted_basis: parseFloat(adjustedBasis),
            capital_gains_rate: parseFloat(capitalGainsRate),
            year: 2025,
          }),
        }
      );
      if (!response.ok) throw new Error("Failed to calculate exit tax");
      const data = await response.json();
      setExitTaxResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePenaltyCalculation = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/form8854/penalty-calculator",
        {
          method: "POST",
          headers: getAuthHeaders(),
          body: JSON.stringify({
            failed_to_file: failedToFile,
            months_late: parseInt(monthsLate) || 0,
          }),
        }
      );
      if (!response.ok) throw new Error("Failed to calculate penalties");
      const data = await response.json();
      setPenaltyResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchOverview = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/form8854/overview",
        {
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) throw new Error("Failed to fetch overview");
      const data = await response.json();
      setOverview(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Form 8854 - Expatriation Tax</h1>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab("filing")}
          className={`px-4 py-2 ${
            activeTab === "filing"
              ? "border-b-2 border-blue-500 font-semibold"
              : ""
          }`}
        >
          Filing Requirement
        </button>
        <button
          onClick={() => setActiveTab("exit-tax")}
          className={`px-4 py-2 ${
            activeTab === "exit-tax"
              ? "border-b-2 border-blue-500 font-semibold"
              : ""
          }`}
        >
          Exit Tax Calculator
        </button>
        <button
          onClick={() => setActiveTab("penalty")}
          className={`px-4 py-2 ${
            activeTab === "penalty"
              ? "border-b-2 border-blue-500 font-semibold"
              : ""
          }`}
        >
          Penalty Calculator
        </button>
        <button
          onClick={() => {
            setActiveTab("overview");
            if (!overview) fetchOverview();
          }}
          className={`px-4 py-2 ${
            activeTab === "overview"
              ? "border-b-2 border-blue-500 font-semibold"
              : ""
          }`}
        >
          Overview
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Filing Requirement Tab */}
      {activeTab === "filing" && (
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-2xl font-semibold mb-4">
            Covered Expatriate Test
          </h2>
          <p className="mb-4 text-gray-600">
            Determine if you are a covered expatriate based on net worth, tax
            liability, or compliance certification.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block font-medium mb-1">
                Net Worth (USD)
              </label>
              <input
                type="number"
                value={netWorth}
                onChange={(e) => setNetWorth(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="e.g., 3000000"
              />
            </div>

            <div>
              <label className="block font-medium mb-1">
                5-Year Average Tax Liability (USD)
              </label>
              <input
                type="number"
                value={fiveYearAvgTax}
                onChange={(e) => setFiveYearAvgTax(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="e.g., 250000"
              />
            </div>

            <div>
              <label className="block font-medium mb-1">
                Years of U.S. Residence (last 15 years)
              </label>
              <input
                type="number"
                value={yearsOfResidence}
                onChange={(e) => setYearsOfResidence(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="e.g., 10"
              />
            </div>

            <button
              onClick={handleFilingRequirement}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? "Calculating..." : "Calculate"}
            </button>
          </div>

          {filingResult && (
            <div className="mt-6 p-4 bg-gray-50 rounded border">
              <h3 className="text-xl font-semibold mb-3">Results</h3>
              <div
                className={`text-lg font-bold mb-4 ${
                  filingResult.covered_expatriate
                    ? "text-red-600"
                    : "text-green-600"
                }`}
              >
                {filingResult.covered_expatriate
                  ? "✗ You are a Covered Expatriate"
                  : "✓ You are NOT a Covered Expatriate"}
              </div>

              <div className="space-y-2">
                <div>
                  <strong>Net Worth Test:</strong>{" "}
                  {filingResult.net_worth_test.exceeds_threshold
                    ? "❌ Exceeds"
                    : "✅ Below"}{" "}
                  threshold (${filingResult.net_worth_test.net_worth.toLocaleString()}{" "}
                  vs ${filingResult.net_worth_test.threshold.toLocaleString()})
                </div>
                <div>
                  <strong>Tax Liability Test:</strong>{" "}
                  {filingResult.tax_liability_test.exceeds_threshold
                    ? "❌ Exceeds"
                    : "✅ Below"}{" "}
                  threshold ($
                  {filingResult.tax_liability_test.five_year_avg_tax.toLocaleString()}{" "}
                  vs $
                  {filingResult.tax_liability_test.threshold.toLocaleString()})
                </div>
                <div>
                  <strong>Long-Term Resident:</strong>{" "}
                  {filingResult.long_term_resident_test.is_long_term_resident
                    ? "✅ Yes"
                    : "❌ No"}{" "}
                  ({filingResult.long_term_resident_test.years_of_residence} of
                  last 15 years, required{" "}
                  {filingResult.long_term_resident_test.required_years})
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Exit Tax Calculator Tab */}
      {activeTab === "exit-tax" && (
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-2xl font-semibold mb-4">
            Exit Tax Calculator (Mark-to-Market)
          </h2>
          <p className="mb-4 text-gray-600">
            Calculate exit tax on unrealized gains with $866,000 exemption
            (2025).
          </p>

          <div className="space-y-4">
            <div>
              <label className="block font-medium mb-1">
                Fair Market Value (USD)
              </label>
              <input
                type="number"
                value={fmv}
                onChange={(e) => setFmv(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="e.g., 2000000"
              />
            </div>

            <div>
              <label className="block font-medium mb-1">
                Adjusted Basis (USD)
              </label>
              <input
                type="number"
                value={adjustedBasis}
                onChange={(e) => setAdjustedBasis(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="e.g., 1000000"
              />
            </div>

            <div>
              <label className="block font-medium mb-1">
                Capital Gains Rate
              </label>
              <input
                type="number"
                step="0.01"
                value={capitalGainsRate}
                onChange={(e) => setCapitalGainsRate(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="e.g., 0.20"
              />
            </div>

            <button
              onClick={handleExitTaxCalculation}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? "Calculating..." : "Calculate Exit Tax"}
            </button>
          </div>

          {exitTaxResult && (
            <div className="mt-6 p-4 bg-gray-50 rounded border">
              <h3 className="text-xl font-semibold mb-3">Exit Tax Calculation</h3>
              <div className="space-y-2">
                <div>
                  <strong>Fair Market Value:</strong> $
                  {exitTaxResult.fair_market_value.toLocaleString()}
                </div>
                <div>
                  <strong>Adjusted Basis:</strong> $
                  {exitTaxResult.adjusted_basis.toLocaleString()}
                </div>
                <div>
                  <strong>Unrealized Gain:</strong> $
                  {exitTaxResult.unrealized_gain.toLocaleString()}
                </div>
                <div>
                  <strong>Exemption (2025):</strong> $
                  {exitTaxResult.exemption.toLocaleString()}
                </div>
                <div>
                  <strong>Exemption Used:</strong> $
                  {exitTaxResult.exemption_used.toLocaleString()}
                </div>
                <div>
                  <strong>Taxable Gain:</strong> $
                  {exitTaxResult.taxable_gain.toLocaleString()}
                </div>
                <div>
                  <strong>Capital Gains Rate:</strong>{" "}
                  {(exitTaxResult.capital_gains_rate * 100).toFixed(0)}%
                </div>
                <div className="text-xl font-bold text-red-600 mt-4">
                  Exit Tax: ${exitTaxResult.exit_tax.toLocaleString()}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Penalty Calculator Tab */}
      {activeTab === "penalty" && (
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-2xl font-semibold mb-4">Penalty Calculator</h2>
          <p className="mb-4 text-gray-600">
            Calculate penalties for failure to file Form 8854.
          </p>

          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={failedToFile}
                  onChange={(e) => setFailedToFile(e.target.checked)}
                  className="mr-2"
                />
                <span className="font-medium">Failed to File Form 8854</span>
              </label>
            </div>

            {failedToFile && (
              <div>
                <label className="block font-medium mb-1">
                  Months Late
                </label>
                <input
                  type="number"
                  value={monthsLate}
                  onChange={(e) => setMonthsLate(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  placeholder="e.g., 12"
                />
              </div>
            )}

            <button
              onClick={handlePenaltyCalculation}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? "Calculating..." : "Calculate Penalties"}
            </button>
          </div>

          {penaltyResult && (
            <div className="mt-6 p-4 bg-gray-50 rounded border">
              <h3 className="text-xl font-semibold mb-3">Penalty Calculation</h3>
              <div className="text-2xl font-bold text-red-600 mb-4">
                Total Penalties: ${penaltyResult.total_penalties.toLocaleString()}
              </div>
              {penaltyResult.penalties.length > 0 && (
                <div className="space-y-2">
                  {penaltyResult.penalties.map((p, idx) => (
                    <div key={idx} className="border-t pt-2">
                      <div>{p.description}</div>
                      <div className="text-sm text-gray-600">
                        Months Late: {p.months_late}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="bg-white p-6 rounded shadow">
          <h2 className="text-2xl font-semibold mb-4">Form 8854 Overview</h2>
          {overview ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold">{overview.form_name}</h3>
                <p className="text-gray-700">{overview.description}</p>
                <p className="text-gray-600 mt-2">{overview.purpose}</p>
              </div>

              <div>
                <h4 className="font-semibold text-lg">
                  Covered Expatriate Tests
                </h4>
                <ul className="list-disc list-inside space-y-1">
                  <li>
                    Net Worth: &gt; $
                    {overview.covered_expatriate_tests.net_worth_threshold.toLocaleString()}
                  </li>
                  <li>
                    Tax Liability: &gt; $
                    {overview.covered_expatriate_tests.tax_liability_threshold_2025.toLocaleString()}{" "}
                    (2025)
                  </li>
                  <li>
                    Long-Term Resident:{" "}
                    {
                      overview.covered_expatriate_tests
                        .long_term_resident_requirement
                    }
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-lg">Exit Tax</h4>
                <ul className="list-disc list-inside space-y-1">
                  <li>
                    Mark-to-Market Exemption (2025): $
                    {overview.exit_tax.mark_to_market_exemption_2025.toLocaleString()}
                  </li>
                  <li>
                    Typical Capital Gains Rate:{" "}
                    {(overview.exit_tax.typical_capital_gains_rate * 100).toFixed(
                      0
                    )}
                    %
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-lg">Penalties</h4>
                <ul className="list-disc list-inside space-y-1">
                  <li>
                    Failure to File: $
                    {overview.penalties.failure_to_file.toLocaleString()}
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-lg">Filing Information</h4>
                <p>{overview.filing_requirement}</p>
                <p>{overview.due_date}</p>
              </div>
            </div>
          ) : (
            <p>Loading overview...</p>
          )}
        </div>
      )}
    </div>
  );
}
