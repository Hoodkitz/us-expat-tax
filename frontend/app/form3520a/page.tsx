"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type TrustType = "GRANTOR" | "NON_GRANTOR" | "SIMPLE" | "COMPLEX";
type DistributionType = "INCOME" | "PRINCIPAL" | "MIXED";

interface FilingRequirementRequest {
  is_us_owner: boolean;
  is_us_beneficiary: boolean;
  trust_name: string;
  trust_country: string;
  tax_year: number;
  has_us_agent: boolean;
}

interface FilingRequirementResult {
  must_file: boolean;
  trust_name: string;
  trust_country: string;
  reasons: string[];
  filing_deadline: string;
  statutory_reference: string;
  beneficiary_statement_deadline: string;
}

interface TrustActivityRequest {
  trust_type: TrustType;
  trust_corpus_usd: number;
  gross_income_usd: number;
  trust_expenses_usd: number;
  distributions_to_us_beneficiaries_usd: number;
  distributions_to_foreign_beneficiaries_usd: number;
  capital_gains_usd: number;
  tax_year: number;
}

interface TrustActivityResult {
  trust_type: TrustType;
  trust_corpus_usd: number;
  gross_income_usd: number;
  net_income_usd: number;
  distributable_net_income_usd: number;
  total_distributions_usd: number;
  distributions_to_us_beneficiaries_usd: number;
  distributions_to_foreign_beneficiaries_usd: number;
  undistributed_income_usd: number;
  reporting_items: string[];
  form_section: string;
}

interface BeneficiaryItem {
  name: string;
  ssn_or_itin: string;
  distribution_amount_usd: number;
  distribution_type: DistributionType;
  is_income_distribution: boolean;
}

interface BeneficiaryReportingRequest {
  beneficiaries: BeneficiaryItem[];
  trust_name: string;
  trust_ein: string;
  tax_year: number;
}

interface BeneficiaryReportingResult {
  trust_name: string;
  trust_ein: string;
  beneficiary_count: number;
  total_distributions_usd: number;
  beneficiaries: BeneficiaryItem[];
  statement_deadline: string;
  statement_requirements: string[];
  form_reference: string;
}

interface PenaltyCalculatorRequest {
  trust_corpus_usd: number;
  months_late: number;
  has_us_agent: boolean;
  books_and_records_provided: boolean;
  tax_year: number;
}

interface PenaltyCalculatorResult {
  base_penalty_usd: number;
  monthly_penalty_usd: number;
  enhanced_penalty_usd: number;
  enhanced_penalty_applicable: boolean;
  total_penalty_usd: number;
  months_late: number;
  penalty_breakdown: string[];
  mitigation_steps: string[];
  statutory_reference: string;
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
    trust_name: "",
    trust_country: "",
    tax_year: new Date().getFullYear() - 1,
    has_us_agent: false,
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
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-gray-400 text-sm">
        Determine whether a foreign trust must file{" "}
        <strong className="text-white">Form 3520-A</strong> and provide
        Beneficiary Statements to US persons.
      </p>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trust Name
            </label>
            <input
              type="text"
              required
              value={form.trust_name}
              onChange={(e) => setForm({ ...form, trust_name: e.target.value })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trust Country (2-letter code)
            </label>
            <input
              type="text"
              required
              maxLength={2}
              value={form.trust_country}
              onChange={(e) => setForm({ ...form, trust_country: e.target.value.toUpperCase() })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Tax Year
            </label>
            <input
              type="number"
              min={2000}
              max={2099}
              value={form.tax_year}
              onChange={(e) => setForm({ ...form, tax_year: parseInt(e.target.value) || 2024 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_us_owner}
              onChange={(e) => setForm({ ...form, is_us_owner: e.target.checked })}
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500"
            />
            <span className="text-sm text-gray-300">
              The trust has a <strong>US owner</strong> (grantor trust under IRC § 671-679)
            </span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_us_beneficiary}
              onChange={(e) => setForm({ ...form, is_us_beneficiary: e.target.checked })}
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500"
            />
            <span className="text-sm text-gray-300">
              The trust has one or more <strong>US beneficiaries</strong>
            </span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.has_us_agent}
              onChange={(e) => setForm({ ...form, has_us_agent: e.target.checked })}
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500"
            />
            <span className="text-sm text-gray-300">
              Trust has designated a <strong>US Agent</strong> for IRS service
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Checking..." : "Check Filing Requirement"}
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-900/30 border border-red-600 rounded-md text-red-300">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="p-5 bg-gray-800 border border-gray-700 rounded-md space-y-4">
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${result.must_file ? "bg-red-900/50 text-red-300" : "bg-green-900/50 text-green-300"}`}>
              {result.must_file ? "FILING REQUIRED" : "NO FILING REQUIRED"}
            </span>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Analysis</h3>
            <ul className="space-y-2">
              {result.reasons.map((r, idx) => (
                <li key={idx} className="text-gray-300 text-sm leading-relaxed">
                  • {r}
                </li>
              ))}
            </ul>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Filing Deadline:</span>
              <p className="text-white font-medium">{result.filing_deadline}</p>
            </div>
            <div>
              <span className="text-gray-400">Beneficiary Statement Deadline:</span>
              <p className="text-white font-medium">{result.beneficiary_statement_deadline}</p>
            </div>
          </div>

          <p className="text-xs text-gray-500 italic">
            Statutory Reference: {result.statutory_reference}
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 2: Trust Activity
// ---------------------------------------------------------------------------

function TrustActivityTab() {
  const [form, setForm] = useState<TrustActivityRequest>({
    trust_type: "COMPLEX",
    trust_corpus_usd: 0,
    gross_income_usd: 0,
    trust_expenses_usd: 0,
    distributions_to_us_beneficiaries_usd: 0,
    distributions_to_foreign_beneficiaries_usd: 0,
    capital_gains_usd: 0,
    tax_year: new Date().getFullYear() - 1,
  });
  const [result, setResult] = useState<TrustActivityResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form3520a/trust-activity`, {
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
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-gray-400 text-sm">
        Calculate trust accounting income and distributions for{" "}
        <strong className="text-white">Form 3520-A Part I</strong>.
      </p>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trust Type
            </label>
            <select
              value={form.trust_type}
              onChange={(e) => setForm({ ...form, trust_type: e.target.value as TrustType })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="GRANTOR">Grantor Trust</option>
              <option value="NON_GRANTOR">Non-Grantor Trust</option>
              <option value="SIMPLE">Simple Trust</option>
              <option value="COMPLEX">Complex Trust</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Tax Year
            </label>
            <input
              type="number"
              min={2000}
              max={2099}
              value={form.tax_year}
              onChange={(e) => setForm({ ...form, tax_year: parseInt(e.target.value) || 2024 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trust Corpus (Total Assets) USD
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={form.trust_corpus_usd}
              onChange={(e) => setForm({ ...form, trust_corpus_usd: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Gross Income USD
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={form.gross_income_usd}
              onChange={(e) => setForm({ ...form, gross_income_usd: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trust Expenses USD
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={form.trust_expenses_usd}
              onChange={(e) => setForm({ ...form, trust_expenses_usd: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Capital Gains USD
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={form.capital_gains_usd}
              onChange={(e) => setForm({ ...form, capital_gains_usd: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Distributions to US Beneficiaries USD
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={form.distributions_to_us_beneficiaries_usd}
              onChange={(e) => setForm({ ...form, distributions_to_us_beneficiaries_usd: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Distributions to Foreign Beneficiaries USD
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={form.distributions_to_foreign_beneficiaries_usd}
              onChange={(e) => setForm({ ...form, distributions_to_foreign_beneficiaries_usd: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Calculating..." : "Calculate Trust Activity"}
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-900/30 border border-red-600 rounded-md text-red-300">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="p-5 bg-gray-800 border border-gray-700 rounded-md space-y-4">
          <h3 className="text-lg font-semibold text-white">Trust Accounting Summary</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Trust Type:</span>
              <p className="text-white font-medium">{result.trust_type}</p>
            </div>
            <div>
              <span className="text-gray-400">Trust Corpus:</span>
              <p className="text-white font-medium">{fmtUSD(result.trust_corpus_usd)}</p>
            </div>
            <div>
              <span className="text-gray-400">Gross Income:</span>
              <p className="text-white font-medium">{fmtUSD(result.gross_income_usd)}</p>
            </div>
            <div>
              <span className="text-gray-400">Net Income:</span>
              <p className="text-white font-medium">{fmtUSD(result.net_income_usd)}</p>
            </div>
            <div>
              <span className="text-gray-400">Distributable Net Income (DNI):</span>
              <p className="text-white font-medium">{fmtUSD(result.distributable_net_income_usd)}</p>
            </div>
            <div>
              <span className="text-gray-400">Total Distributions:</span>
              <p className="text-white font-medium">{fmtUSD(result.total_distributions_usd)}</p>
            </div>
            <div>
              <span className="text-gray-400">Distributions to US Beneficiaries:</span>
              <p className="text-white font-medium">{fmtUSD(result.distributions_to_us_beneficiaries_usd)}</p>
            </div>
            <div>
              <span className="text-gray-400">Undistributed Income:</span>
              <p className="text-white font-medium">{fmtUSD(result.undistributed_income_usd)}</p>
            </div>
          </div>

          <div>
            <h4 className="text-md font-semibold text-white mb-2">Reporting Items</h4>
            <ul className="space-y-1">
              {result.reporting_items.map((item, idx) => (
                <li key={idx} className="text-gray-300 text-sm">
                  • {item}
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-gray-500 italic">
            {result.form_section}
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 3: Beneficiary Reporting
// ---------------------------------------------------------------------------

function BeneficiaryReportingTab() {
  const [form, setForm] = useState<BeneficiaryReportingRequest>({
    beneficiaries: [],
    trust_name: "",
    trust_ein: "",
    tax_year: new Date().getFullYear() - 1,
  });
  const [currentBeneficiary, setCurrentBeneficiary] = useState<BeneficiaryItem>({
    name: "",
    ssn_or_itin: "",
    distribution_amount_usd: 0,
    distribution_type: "INCOME",
    is_income_distribution: true,
  });
  const [result, setResult] = useState<BeneficiaryReportingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const addBeneficiary = () => {
    if (!currentBeneficiary.name || !currentBeneficiary.ssn_or_itin) {
      alert("Please fill in beneficiary name and SSN/ITIN");
      return;
    }
    setForm({ ...form, beneficiaries: [...form.beneficiaries, currentBeneficiary] });
    setCurrentBeneficiary({
      name: "",
      ssn_or_itin: "",
      distribution_amount_usd: 0,
      distribution_type: "INCOME",
      is_income_distribution: true,
    });
  };

  const removeBeneficiary = (idx: number) => {
    setForm({ ...form, beneficiaries: form.beneficiaries.filter((_, i) => i !== idx) });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (form.beneficiaries.length === 0) {
      setError("Please add at least one beneficiary");
      return;
    }
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form3520a/beneficiary-reporting`, {
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
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-gray-400 text-sm">
        Manage Beneficiary Statement obligations for{" "}
        <strong className="text-white">Form 3520-A Part III</strong>.
      </p>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trust Name
            </label>
            <input
              type="text"
              required
              value={form.trust_name}
              onChange={(e) => setForm({ ...form, trust_name: e.target.value })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trust EIN
            </label>
            <input
              type="text"
              required
              value={form.trust_ein}
              onChange={(e) => setForm({ ...form, trust_ein: e.target.value })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Tax Year
          </label>
          <input
            type="number"
            min={2000}
            max={2099}
            value={form.tax_year}
            onChange={(e) => setForm({ ...form, tax_year: parseInt(e.target.value) || 2024 })}
            className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Add beneficiary section */}
        <div className="p-4 bg-gray-900 border border-gray-700 rounded-md space-y-3">
          <h4 className="text-md font-semibold text-white">Add US Beneficiary</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Name</label>
              <input
                type="text"
                value={currentBeneficiary.name}
                onChange={(e) => setCurrentBeneficiary({ ...currentBeneficiary, name: e.target.value })}
                className="w-full px-3 py-2 rounded-md bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">SSN or ITIN</label>
              <input
                type="text"
                value={currentBeneficiary.ssn_or_itin}
                onChange={(e) => setCurrentBeneficiary({ ...currentBeneficiary, ssn_or_itin: e.target.value })}
                className="w-full px-3 py-2 rounded-md bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Distribution Amount USD</label>
              <input
                type="number"
                min={0}
                step="0.01"
                value={currentBeneficiary.distribution_amount_usd}
                onChange={(e) => setCurrentBeneficiary({ ...currentBeneficiary, distribution_amount_usd: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 rounded-md bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Distribution Type</label>
              <select
                value={currentBeneficiary.distribution_type}
                onChange={(e) => setCurrentBeneficiary({ ...currentBeneficiary, distribution_type: e.target.value as DistributionType })}
                className="w-full px-3 py-2 rounded-md bg-gray-800 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="INCOME">Income</option>
                <option value="PRINCIPAL">Principal/Corpus</option>
                <option value="MIXED">Mixed</option>
              </select>
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={currentBeneficiary.is_income_distribution}
              onChange={(e) => setCurrentBeneficiary({ ...currentBeneficiary, is_income_distribution: e.target.checked })}
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500"
            />
            <span className="text-xs text-gray-300">Is Income Distribution</span>
          </label>

          <button
            type="button"
            onClick={addBeneficiary}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium"
          >
            + Add Beneficiary
          </button>
        </div>

        {/* List of added beneficiaries */}
        {form.beneficiaries.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-white">Added Beneficiaries ({form.beneficiaries.length})</h4>
            {form.beneficiaries.map((b, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-900 border border-gray-700 rounded-md">
                <div className="text-sm text-gray-300">
                  <strong>{b.name}</strong> ({b.ssn_or_itin}) — {fmtUSD(b.distribution_amount_usd)} ({b.distribution_type})
                </div>
                <button
                  type="button"
                  onClick={() => removeBeneficiary(idx)}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Calculating..." : "Generate Beneficiary Reporting"}
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-900/30 border border-red-600 rounded-md text-red-300">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="p-5 bg-gray-800 border border-gray-700 rounded-md space-y-4">
          <h3 className="text-lg font-semibold text-white">Beneficiary Statement Requirements</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Trust Name:</span>
              <p className="text-white font-medium">{result.trust_name}</p>
            </div>
            <div>
              <span className="text-gray-400">Trust EIN:</span>
              <p className="text-white font-medium">{result.trust_ein}</p>
            </div>
            <div>
              <span className="text-gray-400">Beneficiary Count:</span>
              <p className="text-white font-medium">{result.beneficiary_count}</p>
            </div>
            <div>
              <span className="text-gray-400">Total Distributions:</span>
              <p className="text-white font-medium">{fmtUSD(result.total_distributions_usd)}</p>
            </div>
            <div>
              <span className="text-gray-400">Statement Deadline:</span>
              <p className="text-white font-medium">{result.statement_deadline}</p>
            </div>
          </div>

          <div>
            <h4 className="text-md font-semibold text-white mb-2">Statement Requirements</h4>
            <ul className="space-y-1">
              {result.statement_requirements.map((req, idx) => (
                <li key={idx} className="text-gray-300 text-sm">
                  • {req}
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-gray-500 italic">
            {result.form_reference}
          </p>
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
    trust_corpus_usd: 0,
    months_late: 0,
    has_us_agent: false,
    books_and_records_provided: false,
    tax_year: new Date().getFullYear() - 1,
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
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-gray-400 text-sm">
        Calculate IRC § 6677 penalties for late/non-filing of{" "}
        <strong className="text-white">Form 3520-A</strong>.
      </p>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Trust Corpus (Total Assets) USD
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              required
              value={form.trust_corpus_usd}
              onChange={(e) => setForm({ ...form, trust_corpus_usd: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Months Late (past deadline)
            </label>
            <input
              type="number"
              min={0}
              max={60}
              value={form.months_late}
              onChange={(e) => setForm({ ...form, months_late: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Tax Year
          </label>
          <input
            type="number"
            min={2000}
            max={2099}
            value={form.tax_year}
            onChange={(e) => setForm({ ...form, tax_year: parseInt(e.target.value) || 2024 })}
            className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.has_us_agent}
              onChange={(e) => setForm({ ...form, has_us_agent: e.target.checked })}
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500"
            />
            <span className="text-sm text-gray-300">
              Trust has designated a <strong>US Agent</strong>
            </span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={form.books_and_records_provided}
              onChange={(e) => setForm({ ...form, books_and_records_provided: e.target.checked })}
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500"
            />
            <span className="text-sm text-gray-300">
              Books and records <strong>provided to IRS</strong> upon request
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Calculating..." : "Calculate Penalties"}
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-900/30 border border-red-600 rounded-md text-red-300">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="p-5 bg-gray-800 border border-gray-700 rounded-md space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Penalty Calculation</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${result.enhanced_penalty_applicable ? "bg-red-900/50 text-red-300" : "bg-yellow-900/50 text-yellow-300"}`}>
              {result.enhanced_penalty_applicable ? "ENHANCED PENALTY" : "STANDARD PENALTY"}
            </span>
          </div>

          <div className="p-4 bg-red-900/20 border border-red-700 rounded-md">
            <div className="text-center">
              <p className="text-sm text-gray-400">Total Penalty</p>
              <p className="text-3xl font-bold text-red-400">{fmtUSD(result.total_penalty_usd)}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Base Penalty:</span>
              <p className="text-white font-medium">{fmtUSD(result.base_penalty_usd)}</p>
            </div>
            <div>
              <span className="text-gray-400">Monthly Penalty:</span>
              <p className="text-white font-medium">{fmtUSD(result.monthly_penalty_usd)}</p>
            </div>
            {result.enhanced_penalty_applicable && (
              <div>
                <span className="text-gray-400">Enhanced Penalty:</span>
                <p className="text-white font-medium">{fmtUSD(result.enhanced_penalty_usd)}</p>
              </div>
            )}
          </div>

          <div>
            <h4 className="text-md font-semibold text-white mb-2">Penalty Breakdown</h4>
            <ul className="space-y-1">
              {result.penalty_breakdown.map((item, idx) => (
                <li key={idx} className="text-gray-300 text-sm">
                  • {item}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-md font-semibold text-white mb-2">Mitigation Steps</h4>
            <ul className="space-y-1">
              {result.mitigation_steps.map((step, idx) => (
                <li key={idx} className="text-gray-300 text-sm">
                  • {step}
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-gray-500 italic">
            {result.statutory_reference}
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function Form3520APage() {
  const [activeTab, setActiveTab] = useState<"filing" | "activity" | "beneficiary" | "penalty">("filing");

  const tabs: { key: typeof activeTab; label: string }[] = [
    { key: "filing", label: "Filing Requirement" },
    { key: "activity", label: "Trust Activity" },
    { key: "beneficiary", label: "Beneficiary Reporting" },
    { key: "penalty", label: "Penalties" },
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Form 3520-A Assistant</h1>
            <p className="text-gray-400 text-sm mt-1">
              Foreign Trust Annual Information Return (IRC § 6048)
            </p>
          </div>
          <Link
            href="/dashboard"
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md text-sm font-medium"
          >
            ← Back to Dashboard
          </Link>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-700">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-blue-500 text-white"
                  : "border-transparent text-gray-400 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
          {activeTab === "filing" && <FilingRequirementTab />}
          {activeTab === "activity" && <TrustActivityTab />}
          {activeTab === "beneficiary" && <BeneficiaryReportingTab />}
          {activeTab === "penalty" && <PenaltyCalculatorTab />}
        </div>
      </div>
    </main>
  );
}
