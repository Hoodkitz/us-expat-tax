"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface Form2441Result {
  max_expenses: string;
  applicable_percentage: string;
  credit_amount: string;
  explanation: string;
  eligible_expenses: string;
  earned_income_limit: string | null;
  is_eligible: boolean;
  num_qualifying_persons: number;
}

interface Form2441Overview {
  form: string;
  title: string;
  purpose: string;
  who_must_file: string[];
  key_rules: string[];
  statutory_references: string[];
  irs_reference: string;
}

interface QualifyingPerson {
  name: string;
  relationship: string;
  age: number;
  is_disabled: boolean;
  care_expenses: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Form2441Page() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Form2441Result | null>(null);
  const [overview, setOverview] = useState<Form2441Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"eligibility" | "calculation">("eligibility");

  // Eligibility tab state
  const [numDependents, setNumDependents] = useState(1);
  const [filingStatus, setFilingStatus] = useState("single");
  const [hasEarnedIncome, setHasEarnedIncome] = useState(true);
  const [bothSpousesWork, setBothSpousesWork] = useState(true);
  const [providerTin, setProviderTin] = useState(true);

  // Calculation tab state
  const [careExpenses, setCareExpenses] = useState("");
  const [agi, setAgi] = useState("");
  const [taxYear, setTaxYear] = useState(2025);
  const [earnedIncome, setEarnedIncome] = useState("");
  const [qualifyingPersons, setQualifyingPersons] = useState<QualifyingPerson[]>([
    { name: "", relationship: "child", age: 5, is_disabled: false, care_expenses: "" },
  ]);

  useEffect(() => {
    fetchOverview();
  }, []);

  async function fetchOverview() {
    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch(`${API_BASE}/api/v1/form2441/overview`, {
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

  function addQualifyingPerson() {
    setQualifyingPersons([
      ...qualifyingPersons,
      { name: "", relationship: "child", age: 5, is_disabled: false, care_expenses: "" },
    ]);
  }

  function updatePerson(index: number, field: keyof QualifyingPerson, value: string | number | boolean) {
    const updated = [...qualifyingPersons];
    updated[index] = { ...updated[index], [field]: value };
    setQualifyingPersons(updated);
  }

  function removePerson(index: number) {
    setQualifyingPersons(qualifyingPersons.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch(`${API_BASE}/api/v1/form2441/calculate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          num_dependents: numDependents,
          care_expenses: careExpenses,
          agi: agi,
          tax_year: taxYear,
          earned_income: earnedIncome || undefined,
          filing_status: filingStatus,
          qualifying_persons: qualifyingPersons.map((p) => ({
            name: p.name,
            relationship: p.relationship,
            age: p.age,
            is_disabled: p.is_disabled,
            care_expenses: p.care_expenses || "0",
          })),
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
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Form 2441</h1>
          <p className="text-gray-600 mb-4">Child and Dependent Care Expenses</p>

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

          {/* Tabs */}
          <div className="mb-6 flex gap-2 border-b">
            <button
              onClick={() => setActiveTab("eligibility")}
              className={`px-4 py-2 font-medium ${
                activeTab === "eligibility"
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Eligibility
            </button>
            <button
              onClick={() => setActiveTab("calculation")}
              className={`px-4 py-2 font-medium ${
                activeTab === "calculation"
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Calculation
            </button>
          </div>

          {/* Eligibility Tab */}
          {activeTab === "eligibility" && (
            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Eligibility Requirements</h3>
                <div className="space-y-3">
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={numDependents > 0}
                      onChange={(e) => setNumDependents(e.target.checked ? 1 : 0)}
                      className="mt-1"
                    />
                    <span className="text-sm text-gray-700">
                      You have at least one qualifying person (child under 13, disabled spouse, or disabled dependent)
                    </span>
                  </label>
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={hasEarnedIncome}
                      onChange={(e) => setHasEarnedIncome(e.target.checked)}
                      className="mt-1"
                    />
                    <span className="text-sm text-gray-700">
                      You (and your spouse if married) have earned income from work or self-employment
                    </span>
                  </label>
                  {filingStatus === "married_joint" && (
                    <label className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={bothSpousesWork}
                        onChange={(e) => setBothSpousesWork(e.target.checked)}
                        className="mt-1"
                      />
                      <span className="text-sm text-gray-700">
                        Both spouses have earned income (or one is a student/disabled)
                      </span>
                    </label>
                  )}
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={providerTin}
                      onChange={(e) => setProviderTin(e.target.checked)}
                      className="mt-1"
                    />
                    <span className="text-sm text-gray-700">
                      You have the care provider&apos;s name, address, and TIN (Taxpayer Identification Number)
                    </span>
                  </label>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Filing Status</h3>
                <select
                  value={filingStatus}
                  onChange={(e) => setFilingStatus(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="single">Single</option>
                  <option value="married_joint">Married Filing Jointly</option>
                  <option value="married_separate">Married Filing Separately</option>
                  <option value="head_of_household">Head of Household</option>
                </select>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-900 mb-2">Key Rules</h3>
                <ul className="text-sm text-yellow-800 space-y-1 list-disc list-inside">
                  <li>Credit is 20-35% of up to $3,000 (one dependent) or $6,000 (two or more)</li>
                  <li>Percentage decreases as AGI increases from $15,000 to $43,000</li>
                  <li>Provider must be identified with TIN</li>
                  <li>Both parents must work (if married filing jointly)</li>
                </ul>
              </div>
            </div>
          )}

          {/* Calculation Tab */}
          {activeTab === "calculation" && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Number of Qualifying Dependents
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={numDependents}
                    onChange={(e) => setNumDependents(parseInt(e.target.value) || 0)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total Care Expenses ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={careExpenses}
                    onChange={(e) => setCareExpenses(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Adjusted Gross Income ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={agi}
                    onChange={(e) => setAgi(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Earned Income ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={earnedIncome}
                    onChange={(e) => setEarnedIncome(e.target.value)}
                    placeholder="Optional - limits credit"
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
                    onChange={(e) => setTaxYear(parseInt(e.target.value) || 2025)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
              </div>

              {/* Qualifying Persons */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">Qualifying Persons</h3>
                  <button
                    type="button"
                    onClick={addQualifyingPerson}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    + Add Person
                  </button>
                </div>
                <div className="space-y-3">
                  {qualifyingPersons.map((person, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
                          <input
                            type="text"
                            value={person.name}
                            onChange={(e) => updatePerson(index, "name", e.target.value)}
                            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Relationship</label>
                          <select
                            value={person.relationship}
                            onChange={(e) => updatePerson(index, "relationship", e.target.value)}
                            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                          >
                            <option value="child">Child</option>
                            <option value="spouse">Spouse</option>
                            <option value="dependent">Dependent</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Age</label>
                          <input
                            type="number"
                            min="0"
                            value={person.age}
                            onChange={(e) => updatePerson(index, "age", parseInt(e.target.value) || 0)}
                            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Disabled</label>
                          <input
                            type="checkbox"
                            checked={person.is_disabled}
                            onChange={(e) => updatePerson(index, "is_disabled", e.target.checked)}
                            className="mt-1"
                          />
                        </div>
                      </div>
                      <div className="mt-2 flex justify-end">
                        <button
                          type="button"
                          onClick={() => removePerson(index)}
                          className="text-xs text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Calculating..." : "Calculate Credit"}
              </button>
            </form>
          )}

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
                  <span className="font-medium">Max Expenses:</span> $
                  {parseFloat(result.max_expenses).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Applicable Percentage:</span>{" "}
                  {parseFloat(result.applicable_percentage).toFixed(0)}%
                </div>
                <div>
                  <span className="font-medium">Credit Amount:</span> $
                  {parseFloat(result.credit_amount).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Eligible Expenses:</span> $
                  {parseFloat(result.eligible_expenses).toLocaleString()}
                </div>
                {result.earned_income_limit && (
                  <div>
                    <span className="font-medium">Earned Income Limit:</span> $
                    {parseFloat(result.earned_income_limit).toLocaleString()}
                  </div>
                )}
                <div>
                  <span className="font-medium">Qualifying Persons:</span>{" "}
                  {result.num_qualifying_persons}
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
