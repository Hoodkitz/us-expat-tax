"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type TrustType = "FOREIGN_GRANTOR" | "NON_GRANTOR";
type IncomeType = "INTEREST" | "DIVIDENDS" | "CAPITAL_GAINS" | "RENTAL" | "OTHER";

interface FilingRequirementRequest {
  is_us_owner: boolean;
  is_us_beneficiary: boolean;
  trust_type: TrustType;
  received_distribution: boolean;
  distribution_amount_usd: number;
}

interface FilingRequirementResult {
  filing_required: boolean;
  filer_role: string | null;
  trust_type: TrustType;
  reasons: string[];
  us_owner: boolean;
  us_beneficiary: boolean;
}

interface DistributionItem {
  income_type: IncomeType;
  gross_amount_usd: number;
  withholding_tax_usd: number;
  distribution_date: string;
  source_country: string;
}

interface IncomeDistributionRequest {
  trust_type: TrustType;
  distributions: DistributionItem[];
}

interface IncomeDistributionResult {
  trust_type: TrustType;
  total_distributions: number;
  total_gross_usd: number;
  total_withholding_usd: number;
  total_net_usd: number;
  by_income_type: Record<string, {
    count: number;
    gross_usd: number;
    withholding_usd: number;
    net_usd: number;
  }>;
  tax_treatment: string;
  distributions: DistributionItem[];
}

interface ForeignGrantorStatementRequest {
  trust_name: string;
  trust_ein: string;
  trust_country: string;
  us_owner_name: string;
  us_owner_ssn: string;
  tax_year: number;
  trust_assets_usd: number;
  trust_income_usd: number;
  trust_distributions_usd: number;
}

interface ForeignGrantorStatementResult {
  statement_type: string;
  trust_name: string;
  trust_ein: string;
  trust_country: string;
  tax_year: number;
  us_owner_name: string;
  us_owner_ssn: string;
  trust_assets_usd: number;
  trust_income_usd: number;
  trust_distributions_usd: number;
  statement_date: string;
  owner_obligations: string[];
  grantor_trust_rules: string;
}

interface PenaltyCalculatorRequest {
  filing_deadline: string;
  actual_filing_date: string | null;
  trust_gross_value_usd: number;
  is_initial_failure: boolean;
}

interface PenaltyDetail {
  type: string;
  rate: string;
  amount_usd: number;
  description: string;
  periods?: number;
}

interface PenaltyCalculatorResult {
  filing_deadline: string;
  actual_filing_date: string | null;
  days_late: number;
  trust_gross_value_usd: number;
  penalties: PenaltyDetail[];
  total_penalty_usd: number;
  penalty_rate: string;
  maximum_penalty_usd: number;
  penalty_capped: boolean;
  statute: string;
  notes: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function fmtUSD(val: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(val);
}

// ---------------------------------------------------------------------------
// Tab 1: Filing Requirement
// ---------------------------------------------------------------------------

function FilingRequirementTab() {
  const [form, setForm] = useState<FilingRequirementRequest>({
    is_us_owner: false,
    is_us_beneficiary: false,
    trust_type: "FOREIGN_GRANTOR",
    received_distribution: false,
    distribution_amount_usd: 0,
  });
  const [result, setResult] = useState<FilingRequirementResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form3520a/filing-requirement`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail ?? `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      setResult(data.result);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Filing Requirement</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_us_owner"
              checked={form.is_us_owner}
              onChange={(e) => setForm({ ...form, is_us_owner: e.target.checked })}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <label htmlFor="is_us_owner" className="text-sm font-medium text-gray-700">
              Trust has at least one U.S. owner (grantor)
            </label>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_us_beneficiary"
              checked={form.is_us_beneficiary}
              onChange={(e) => setForm({ ...form, is_us_beneficiary: e.target.checked })}
              className="h-4 w-4 text-blue-600 rounded"
            />
            <label htmlFor="is_us_beneficiary" className="text-sm font-medium text-gray-700">
              Trust has at least one U.S. beneficiary
            </label>
          </div>
        </div>

        <div>
          <label htmlFor="trust_type" className="block text-sm font-medium text-gray-700 mb-1">
            Trust Type
          </label>
          <select
            id="trust_type"
            value={form.trust_type}
            onChange={(e) => setForm({ ...form, trust_type: e.target.value as TrustType })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="FOREIGN_GRANTOR">Foreign Grantor Trust</option>
            <option value="NON_GRANTOR">Non-Grantor Trust</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="received_distribution"
            checked={form.received_distribution}
            onChange={(e) => setForm({ ...form, received_distribution: e.target.checked })}
            className="h-4 w-4 text-blue-600 rounded"
          />
          <label htmlFor="received_distribution" className="text-sm font-medium text-gray-700">
            Beneficiary received a distribution
          </label>
        </div>

        {form.received_distribution && (
          <div>
            <label htmlFor="distribution_amount" className="block text-sm font-medium text-gray-700 mb-1">
              Distribution Amount (USD)
            </label>
            <input
              type="number"
              id="distribution_amount"
              value={form.distribution_amount_usd}
              onChange={(e) => setForm({ ...form, distribution_amount_usd: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Checking..." : "Check Filing Requirement"}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">Result</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              result.filing_required ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
            }`}>
              {result.filing_required ? 'Filing Required' : 'No Filing Required'}
            </span>
          </div>

          {result.filer_role && (
            <div>
              <span className="font-medium text-gray-700">Filer Role: </span>
              <span className="text-gray-900">{result.filer_role}</span>
            </div>
          )}

          <div>
            <span className="font-medium text-gray-700">Trust Type: </span>
            <span className="text-gray-900">{result.trust_type.replace('_', ' ')}</span>
          </div>

          <div>
            <h4 className="font-medium text-gray-700 mb-2">Reasons:</h4>
            <ul className="list-disc list-inside space-y-1 text-gray-900">
              {result.reasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 2: Income Distribution
// ---------------------------------------------------------------------------

function IncomeDistributionTab() {
  const [trustType, setTrustType] = useState<TrustType>("NON_GRANTOR");
  const [distributions, setDistributions] = useState<DistributionItem[]>([{
    income_type: "DIVIDENDS",
    gross_amount_usd: 0,
    withholding_tax_usd: 0,
    distribution_date: new Date().toISOString().split('T')[0],
    source_country: "CH",
  }]);
  const [result, setResult] = useState<IncomeDistributionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const addDistribution = () => {
    setDistributions([...distributions, {
      income_type: "DIVIDENDS",
      gross_amount_usd: 0,
      withholding_tax_usd: 0,
      distribution_date: new Date().toISOString().split('T')[0],
      source_country: "CH",
    }]);
  };

  const removeDistribution = (index: number) => {
    setDistributions(distributions.filter((_, i) => i !== index));
  };

  const updateDistribution = (index: number, field: keyof DistributionItem, value: any) => {
    const updated = [...distributions];
    updated[index] = { ...updated[index], [field]: value };
    setDistributions(updated);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form3520a/income-distribution`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ trust_type: trustType, distributions }),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail ?? `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      setResult(data.result);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Income Distribution</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="trust_type_income" className="block text-sm font-medium text-gray-700 mb-1">
            Trust Type
          </label>
          <select
            id="trust_type_income"
            value={trustType}
            onChange={(e) => setTrustType(e.target.value as TrustType)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="FOREIGN_GRANTOR">Foreign Grantor Trust</option>
            <option value="NON_GRANTOR">Non-Grantor Trust</option>
          </select>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">Distributions</h3>
            <button
              type="button"
              onClick={addDistribution}
              className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-1 px-3 rounded"
            >
              + Add Distribution
            </button>
          </div>

          {distributions.map((dist, idx) => (
            <div key={idx} className="border border-gray-300 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-700">Distribution {idx + 1}</h4>
                {distributions.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeDistribution(idx)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Income Type</label>
                  <select
                    value={dist.income_type}
                    onChange={(e) => updateDistribution(idx, 'income_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="INTEREST">Interest</option>
                    <option value="DIVIDENDS">Dividends</option>
                    <option value="CAPITAL_GAINS">Capital Gains</option>
                    <option value="RENTAL">Rental Income</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Distribution Date</label>
                  <input
                    type="date"
                    value={dist.distribution_date}
                    onChange={(e) => updateDistribution(idx, 'distribution_date', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Gross Amount (USD)</label>
                  <input
                    type="number"
                    value={dist.gross_amount_usd}
                    onChange={(e) => updateDistribution(idx, 'gross_amount_usd', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Withholding Tax (USD)</label>
                  <input
                    type="number"
                    value={dist.withholding_tax_usd}
                    onChange={(e) => updateDistribution(idx, 'withholding_tax_usd', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Source Country</label>
                  <input
                    type="text"
                    value={dist.source_country}
                    onChange={(e) => updateDistribution(idx, 'source_country', e.target.value)}
                    maxLength={2}
                    placeholder="CH"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Calculating..." : "Calculate Income Distribution"}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Distribution Summary</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <div className="text-sm text-gray-600">Total Gross</div>
              <div className="text-xl font-bold text-gray-900">{fmtUSD(result.total_gross_usd)}</div>
            </div>
            <div className="bg-red-50 p-4 rounded">
              <div className="text-sm text-gray-600">Total Withholding</div>
              <div className="text-xl font-bold text-gray-900">{fmtUSD(result.total_withholding_usd)}</div>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <div className="text-sm text-gray-600">Total Net</div>
              <div className="text-xl font-bold text-gray-900">{fmtUSD(result.total_net_usd)}</div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-700 mb-2">By Income Type</h4>
            <div className="space-y-2">
              {Object.entries(result.by_income_type).map(([type, data]) => (
                <div key={type} className="border border-gray-200 rounded p-3">
                  <div className="font-medium text-gray-800">{type.replace('_', ' ')}</div>
                  <div className="text-sm text-gray-600">
                    Count: {data.count} | Gross: {fmtUSD(data.gross_usd)} | Net: {fmtUSD(data.net_usd)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
            <div className="font-medium text-gray-800 mb-1">Tax Treatment</div>
            <div className="text-sm text-gray-700">{result.tax_treatment}</div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 3: Foreign Grantor Statement
// ---------------------------------------------------------------------------

function ForeignGrantorStatementTab() {
  const [form, setForm] = useState<ForeignGrantorStatementRequest>({
    trust_name: "",
    trust_ein: "",
    trust_country: "CH",
    us_owner_name: "",
    us_owner_ssn: "",
    tax_year: new Date().getFullYear() - 1,
    trust_assets_usd: 0,
    trust_income_usd: 0,
    trust_distributions_usd: 0,
  });
  const [result, setResult] = useState<ForeignGrantorStatementResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form3520a/foreign-grantor-statement`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail ?? `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      setResult(data.result);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Foreign Grantor Trust Statement</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="trust_name" className="block text-sm font-medium text-gray-700 mb-1">
              Trust Name
            </label>
            <input
              type="text"
              id="trust_name"
              value={form.trust_name}
              onChange={(e) => setForm({ ...form, trust_name: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="trust_ein" className="block text-sm font-medium text-gray-700 mb-1">
              Trust EIN
            </label>
            <input
              type="text"
              id="trust_ein"
              value={form.trust_ein}
              onChange={(e) => setForm({ ...form, trust_ein: e.target.value })}
              placeholder="98-7654321"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="trust_country" className="block text-sm font-medium text-gray-700 mb-1">
              Trust Country (ISO Code)
            </label>
            <input
              type="text"
              id="trust_country"
              value={form.trust_country}
              onChange={(e) => setForm({ ...form, trust_country: e.target.value })}
              maxLength={2}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="tax_year" className="block text-sm font-medium text-gray-700 mb-1">
              Tax Year
            </label>
            <input
              type="number"
              id="tax_year"
              value={form.tax_year}
              onChange={(e) => setForm({ ...form, tax_year: parseInt(e.target.value) })}
              min={2000}
              max={2099}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="us_owner_name" className="block text-sm font-medium text-gray-700 mb-1">
              U.S. Owner Name
            </label>
            <input
              type="text"
              id="us_owner_name"
              value={form.us_owner_name}
              onChange={(e) => setForm({ ...form, us_owner_name: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="us_owner_ssn" className="block text-sm font-medium text-gray-700 mb-1">
              U.S. Owner SSN
            </label>
            <input
              type="text"
              id="us_owner_ssn"
              value={form.us_owner_ssn}
              onChange={(e) => setForm({ ...form, us_owner_ssn: e.target.value })}
              placeholder="123-45-6789"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="trust_assets" className="block text-sm font-medium text-gray-700 mb-1">
              Trust Assets (USD)
            </label>
            <input
              type="number"
              id="trust_assets"
              value={form.trust_assets_usd}
              onChange={(e) => setForm({ ...form, trust_assets_usd: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="trust_income" className="block text-sm font-medium text-gray-700 mb-1">
              Trust Income (USD)
            </label>
            <input
              type="number"
              id="trust_income"
              value={form.trust_income_usd}
              onChange={(e) => setForm({ ...form, trust_income_usd: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="trust_distributions" className="block text-sm font-medium text-gray-700 mb-1">
              Trust Distributions (USD)
            </label>
            <input
              type="number"
              id="trust_distributions"
              value={form.trust_distributions_usd}
              onChange={(e) => setForm({ ...form, trust_distributions_usd: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Generating..." : "Generate Statement"}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Foreign Grantor Trust Owner Statement</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Trust Name: </span>
              <span className="text-gray-900">{result.trust_name}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Trust EIN: </span>
              <span className="text-gray-900">{result.trust_ein}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Country: </span>
              <span className="text-gray-900">{result.trust_country}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Tax Year: </span>
              <span className="text-gray-900">{result.tax_year}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">U.S. Owner: </span>
              <span className="text-gray-900">{result.us_owner_name}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Trust Assets: </span>
              <span className="text-gray-900">{fmtUSD(result.trust_assets_usd)}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Trust Income: </span>
              <span className="text-gray-900">{fmtUSD(result.trust_income_usd)}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Distributions: </span>
              <span className="text-gray-900">{fmtUSD(result.trust_distributions_usd)}</span>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-700 mb-2">Owner Obligations:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-900">
              {result.owner_obligations.map((obligation, idx) => (
                <li key={idx}>{obligation}</li>
              ))}
            </ul>
          </div>

          <div className="bg-blue-50 border border-blue-200 p-4 rounded">
            <div className="font-medium text-gray-800 mb-1">Grantor Trust Rules</div>
            <div className="text-sm text-gray-700">{result.grantor_trust_rules}</div>
          </div>

          <div className="text-xs text-gray-500">
            Statement Date: {result.statement_date}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 4: Penalty Calculator
// ---------------------------------------------------------------------------

function PenaltyCalculatorTab() {
  const [form, setForm] = useState<PenaltyCalculatorRequest>({
    filing_deadline: new Date(new Date().getFullYear(), 2, 15).toISOString().split('T')[0], // March 15
    actual_filing_date: null,
    trust_gross_value_usd: 0,
    is_initial_failure: true,
  });
  const [result, setResult] = useState<PenaltyCalculatorResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form3520a/penalty-calculator`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail ?? `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      setResult(data.result);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Penalty Calculator (IRC §6677)</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="filing_deadline" className="block text-sm font-medium text-gray-700 mb-1">
              Filing Deadline
            </label>
            <input
              type="date"
              id="filing_deadline"
              value={form.filing_deadline}
              onChange={(e) => setForm({ ...form, filing_deadline: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="actual_filing_date" className="block text-sm font-medium text-gray-700 mb-1">
              Actual Filing Date (leave empty if not filed)
            </label>
            <input
              type="date"
              id="actual_filing_date"
              value={form.actual_filing_date || ""}
              onChange={(e) => setForm({ ...form, actual_filing_date: e.target.value || null })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="trust_value" className="block text-sm font-medium text-gray-700 mb-1">
              Trust Gross Value (USD)
            </label>
            <input
              type="number"
              id="trust_value"
              value={form.trust_gross_value_usd}
              onChange={(e) => setForm({ ...form, trust_gross_value_usd: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Calculating..." : "Calculate Penalty"}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Penalty Calculation</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-red-50 p-4 rounded">
              <div className="text-sm text-gray-600">Total Penalty</div>
              <div className="text-2xl font-bold text-red-700">{fmtUSD(result.total_penalty_usd)}</div>
              <div className="text-xs text-gray-600 mt-1">{result.penalty_rate} of trust value</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded">
              <div className="text-sm text-gray-600">Days Late</div>
              <div className="text-2xl font-bold text-yellow-700">{result.days_late}</div>
            </div>
            <div className="bg-blue-50 p-4 rounded">
              <div className="text-sm text-gray-600">Trust Value</div>
              <div className="text-2xl font-bold text-blue-700">{fmtUSD(result.trust_gross_value_usd)}</div>
            </div>
          </div>

          {result.penalties.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Penalty Breakdown:</h4>
              <div className="space-y-2">
                {result.penalties.map((penalty, idx) => (
                  <div key={idx} className="border border-gray-200 rounded p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-800">
                        {penalty.type.replace('_', ' ')}
                      </span>
                      <span className="font-bold text-red-700">{fmtUSD(penalty.amount_usd)}</span>
                    </div>
                    <div className="text-sm text-gray-600">{penalty.description}</div>
                    <div className="text-xs text-gray-500 mt-1">Rate: {penalty.rate}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.penalty_capped && (
            <div className="bg-orange-50 border border-orange-200 p-4 rounded">
              <div className="font-medium text-orange-800">⚠️ Penalty Capped at Maximum</div>
              <div className="text-sm text-orange-700">
                Maximum penalty: {fmtUSD(result.maximum_penalty_usd)} (25% of trust value)
              </div>
            </div>
          )}

          <div className="bg-gray-50 border border-gray-200 p-4 rounded">
            <div className="font-medium text-gray-800 mb-2">Notes:</div>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {result.notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
            </ul>
          </div>

          <div className="text-xs text-gray-500">
            Statute: {result.statute}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function Form3520APage() {
  const [activeTab, setActiveTab] = useState<"requirement" | "income" | "grantor" | "penalty">("requirement");

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="mb-8">
          <Link href="/" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mt-4">
            Form 3520-A: Foreign Trust Annual Information Return
          </h1>
          <p className="text-gray-600 mt-2">
            Annual Information Return of Foreign Trust With a U.S. Owner
          </p>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab("requirement")}
                className={`px-6 py-3 font-medium text-sm border-b-2 ${
                  activeTab === "requirement"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300"
                }`}
              >
                Filing Requirement
              </button>
              <button
                onClick={() => setActiveTab("income")}
                className={`px-6 py-3 font-medium text-sm border-b-2 ${
                  activeTab === "income"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300"
                }`}
              >
                Income Distribution
              </button>
              <button
                onClick={() => setActiveTab("grantor")}
                className={`px-6 py-3 font-medium text-sm border-b-2 ${
                  activeTab === "grantor"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300"
                }`}
              >
                Foreign Grantor
              </button>
              <button
                onClick={() => setActiveTab("penalty")}
                className={`px-6 py-3 font-medium text-sm border-b-2 ${
                  activeTab === "penalty"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300"
                }`}
              >
                Penalty Calculator
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === "requirement" && <FilingRequirementTab />}
            {activeTab === "income" && <IncomeDistributionTab />}
            {activeTab === "grantor" && <ForeignGrantorStatementTab />}
            {activeTab === "penalty" && <PenaltyCalculatorTab />}
          </div>
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">📋 About Form 3520-A</h2>
          <p className="text-sm text-blue-800 mb-3">
            Form 3520-A is filed by a foreign trust with a U.S. owner (or its U.S. agent) to report
            information about the trust's operations, assets, and income.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <div className="font-medium mb-1">Foreign Grantor Trust:</div>
              <ul className="list-disc list-inside space-y-1">
                <li>Income taxed to U.S. grantor/owner</li>
                <li>Owner reports trust income on Form 1040</li>
                <li>Must provide statement to beneficiaries</li>
              </ul>
            </div>
            <div>
              <div className="font-medium mb-1">Non-Grantor Trust:</div>
              <ul className="list-disc list-inside space-y-1">
                <li>Distributions taxed to U.S. beneficiaries</li>
                <li>Trust files Form 3520-A for distributions</li>
                <li>Beneficiary reports on Form 3520</li>
              </ul>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-blue-200">
            <div className="font-medium text-blue-900 mb-1">Penalties (IRC §6677):</div>
            <ul className="list-disc list-inside space-y-1 text-sm text-blue-800">
              <li>Initial failure: 5% of gross trust value</li>
              <li>Continuing failure after 90 days: Additional 5% per 30-day period</li>
              <li>Maximum penalty: 25% of gross trust value</li>
              <li>Due date: March 15 (with 6-month extension available via Form 7004)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
