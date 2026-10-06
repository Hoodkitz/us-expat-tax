"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FilingRequirementRequest {
  treaty_country: string;
  treaty_article: string;
  position_type: string;
}

interface FilingRequirementResult {
  required: boolean;
  reason: string;
  filing_deadline: string;
  penalty_if_not_filed: number;
  treaty_country_name: string;
  position_type: string;
}

interface DisclosureRequest {
  treaty_country: string;
  treaty_article: string;
  treaty_provision: string;
  taxpayer_position: string;
  law_overruled: string;
}

interface DisclosureResult {
  disclosure_summary: string;
  reporting_requirements: string[];
  treaty_reference: string;
  penalty_warning: string;
}

interface OverviewResult {
  description: string;
  common_countries: Record<string, string>;
  common_articles: Record<string, string>;
  filing_threshold: string;
  penalty_amount: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function fmtUSD(val: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(val);
}

// ---------------------------------------------------------------------------
// Filing Requirement Tab
// ---------------------------------------------------------------------------

function FilingRequirementTab() {
  const [form, setForm] = useState<FilingRequirementRequest>({
    treaty_country: "DE",
    treaty_article: "Article 4",
    position_type: "RESIDENCE",
  });
  const [result, setResult] = useState<FilingRequirementResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/form8833/filing-requirement`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errData.detail || "Request failed");
      }

      const data: FilingRequirementResult = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Form 8833 Filing Requirement</h3>
        <p className="text-sm text-blue-800">
          Check if you need to file Form 8833 when taking a treaty position that overrides U.S. tax law.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Treaty Country</label>
          <select
            value={form.treaty_country}
            onChange={(e) => setForm({ ...form, treaty_country: e.target.value })}
            className="w-full border rounded px-3 py-2"
            required
          >
            <option value="DE">Germany</option>
            <option value="GB">United Kingdom</option>
            <option value="CA">Canada</option>
            <option value="FR">France</option>
            <option value="JP">Japan</option>
            <option value="AU">Australia</option>
            <option value="CH">Switzerland</option>
            <option value="NL">Netherlands</option>
            <option value="IE">Ireland</option>
            <option value="IN">India</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Treaty Article</label>
          <input
            type="text"
            value={form.treaty_article}
            onChange={(e) => setForm({ ...form, treaty_article: e.target.value })}
            className="w-full border rounded px-3 py-2"
            placeholder="e.g., Article 4, Article 15"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Position Type</label>
          <select
            value={form.position_type}
            onChange={(e) => setForm({ ...form, position_type: e.target.value })}
            className="w-full border rounded px-3 py-2"
            required
          >
            <option value="RESIDENCE">Residence</option>
            <option value="BUSINESS_PROFITS">Business Profits</option>
            <option value="DIVIDENDS">Dividends</option>
            <option value="INTEREST">Interest</option>
            <option value="ROYALTIES">Royalties</option>
            <option value="PENSIONS">Pensions</option>
            <option value="GOVERNMENT_SERVICE">Government Service</option>
            <option value="STUDENTS_TEACHERS">Students/Teachers</option>
            <option value="OTHER_INCOME">Other Income</option>
            <option value="TOTALIZATION">Totalization (Social Security)</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded disabled:opacity-50"
        >
          {loading ? "Checking..." : "Check Filing Requirement"}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 text-red-800">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="bg-white border rounded-lg p-6 space-y-4">
          <div className={`p-4 rounded ${result.required ? "bg-yellow-50 border border-yellow-200" : "bg-green-50 border border-green-200"}`}>
            <h4 className={`font-semibold ${result.required ? "text-yellow-900" : "text-green-900"}`}>
              {result.required ? "⚠️ Filing Required" : "✓ Filing Not Required"}
            </h4>
          </div>

          <div>
            <strong>Treaty Country:</strong> {result.treaty_country_name}
          </div>

          <div>
            <strong>Position Type:</strong> {result.position_type}
          </div>

          <div>
            <strong>Reason:</strong>
            <p className="mt-1 text-sm text-gray-700">{result.reason}</p>
          </div>

          <div>
            <strong>Filing Deadline:</strong> {result.filing_deadline}
          </div>

          {result.required && (
            <div className="bg-red-50 border border-red-200 rounded p-4">
              <strong className="text-red-900">Penalty if not filed:</strong>{" "}
              <span className="text-red-900 font-bold">{fmtUSD(result.penalty_if_not_filed)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Position Disclosure Tab
// ---------------------------------------------------------------------------

function DisclosureTab() {
  const [form, setForm] = useState<DisclosureRequest>({
    treaty_country: "DE",
    treaty_article: "Article 4",
    treaty_provision: "",
    taxpayer_position: "",
    law_overruled: "",
  });
  const [result, setResult] = useState<DisclosureResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/form8833/disclosure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errData.detail || "Request failed");
      }

      const data: DisclosureResult = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Treaty Position Disclosure</h3>
        <p className="text-sm text-blue-800">
          Create a disclosure statement for your treaty-based return position.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Treaty Country</label>
          <select
            value={form.treaty_country}
            onChange={(e) => setForm({ ...form, treaty_country: e.target.value })}
            className="w-full border rounded px-3 py-2"
            required
          >
            <option value="DE">Germany</option>
            <option value="GB">United Kingdom</option>
            <option value="CA">Canada</option>
            <option value="FR">France</option>
            <option value="JP">Japan</option>
            <option value="AU">Australia</option>
            <option value="CH">Switzerland</option>
            <option value="NL">Netherlands</option>
            <option value="IE">Ireland</option>
            <option value="IN">India</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Treaty Article</label>
          <input
            type="text"
            value={form.treaty_article}
            onChange={(e) => setForm({ ...form, treaty_article: e.target.value })}
            className="w-full border rounded px-3 py-2"
            placeholder="e.g., Article 4"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Treaty Provision</label>
          <textarea
            value={form.treaty_provision}
            onChange={(e) => setForm({ ...form, treaty_provision: e.target.value })}
            className="w-full border rounded px-3 py-2"
            rows={3}
            placeholder="Specific treaty text or provision you rely upon..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Your Position</label>
          <textarea
            value={form.taxpayer_position}
            onChange={(e) => setForm({ ...form, taxpayer_position: e.target.value })}
            className="w-full border rounded px-3 py-2"
            rows={4}
            placeholder="Explain your position and how the treaty applies to your situation..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">U.S. Law Overruled</label>
          <input
            type="text"
            value={form.law_overruled}
            onChange={(e) => setForm({ ...form, law_overruled: e.target.value })}
            className="w-full border rounded px-3 py-2"
            placeholder="e.g., IRC §7701(b)"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded disabled:opacity-50"
        >
          {loading ? "Creating..." : "Create Disclosure"}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 text-red-800">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="bg-white border rounded-lg p-6 space-y-4">
          <div>
            <strong className="text-lg">Disclosure Summary</strong>
            <p className="mt-2 text-sm text-gray-700">{result.disclosure_summary}</p>
          </div>

          <div>
            <strong>Treaty Reference:</strong> {result.treaty_reference}
          </div>

          <div>
            <strong>Reporting Requirements:</strong>
            <ul className="mt-2 space-y-1 text-sm text-gray-700">
              {result.reporting_requirements.map((req, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-red-50 border border-red-200 rounded p-4">
            <strong className="text-red-900">⚠️ Penalty Warning</strong>
            <p className="mt-2 text-sm text-red-800">{result.penalty_warning}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Info Tab
// ---------------------------------------------------------------------------

function InfoTab() {
  const [overview, setOverview] = useState<OverviewResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/form8833/overview`);
      if (!res.ok) throw new Error("Failed to fetch overview");

      const data: OverviewResult = await res.json();
      setOverview(data);
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  if (!overview && !loading && !error) {
    return (
      <div className="text-center py-12">
        <button
          onClick={fetchOverview}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded"
        >
          Load Form 8833 Overview
        </button>
      </div>
    );
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-600">Loading overview...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-4 text-red-800">
        <strong>Error:</strong> {error}
      </div>
    );
  }

  if (!overview) return null;

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">What is Form 8833?</h3>
        <p className="text-sm text-blue-800">{overview.description}</p>
      </div>

      <div className="bg-white border rounded-lg p-6">
        <h4 className="font-semibold mb-3">Common Treaty Countries</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {Object.entries(overview.common_countries).map(([code, name]) => (
            <div key={code} className="flex items-center">
              <span className="font-medium text-blue-600 mr-2">{code}:</span>
              <span>{name}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white border rounded-lg p-6">
        <h4 className="font-semibold mb-3">Common Treaty Articles</h4>
        <div className="space-y-2 text-sm">
          {Object.entries(overview.common_articles).map(([article, description]) => (
            <div key={article}>
              <strong className="text-blue-600">{article}:</strong> {description}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="font-semibold text-yellow-900 mb-2">Filing Threshold</h4>
        <p className="text-sm text-yellow-800">{overview.filing_threshold}</p>
      </div>

      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h4 className="font-semibold text-red-900 mb-2">Penalty for Non-Filing</h4>
        <p className="text-lg font-bold text-red-900">{fmtUSD(overview.penalty_amount)} per failure to disclose</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function Form8833Page() {
  const [activeTab, setActiveTab] = useState<"filing" | "disclosure" | "info">("filing");

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-6">
          <Link href="/" className="text-blue-600 hover:underline text-sm">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold mt-4 mb-2">Form 8833</h1>
          <p className="text-gray-600">Treaty-Based Return Position Disclosure</p>
        </div>

        {/* Tabs */}
        <div className="bg-white border-b mb-6">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab("filing")}
              className={`py-4 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "filing"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              Filing Requirement
            </button>
            <button
              onClick={() => setActiveTab("disclosure")}
              className={`py-4 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "disclosure"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              Position Disclosure
            </button>
            <button
              onClick={() => setActiveTab("info")}
              className={`py-4 border-b-2 font-medium text-sm transition-colors ${
                activeTab === "info"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              Info
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow p-6">
          {activeTab === "filing" && <FilingRequirementTab />}
          {activeTab === "disclosure" && <DisclosureTab />}
          {activeTab === "info" && <InfoTab />}
        </div>
      </div>
    </div>
  );
}
