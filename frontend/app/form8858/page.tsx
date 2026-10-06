"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FilingRequirementRequest {
  ownership_type: "direct_fde" | "indirect_fde" | "foreign_branch" | "cfc_fde";
  ownership_percentage: number;
  is_us_person: boolean;
  entity_country: string;
  tax_year: number;
}

interface FilingRequirementResult {
  must_file: boolean;
  reason: string;
  form_due_date: string;
  penalty_if_not_filed_usd: number;
  filing_instructions: string;
}

interface IncomeSummaryRequest {
  gross_receipts_usd: number;
  cost_of_goods_sold_usd: number;
  operating_expenses_usd: number;
  depreciation_usd: number;
  other_income_usd: number;
  other_deductions_usd: number;
}

interface IncomeSummaryResult {
  gross_income_usd: number;
  total_deductions_usd: number;
  net_income_loss_usd: number;
  is_profitable: boolean;
  us_tax_implications: string;
}

interface PenaltyRequest {
  years_not_filed: number;
  continued_failure_periods: number;
}

interface PenaltyResult {
  base_penalty_usd: number;
  continuation_penalty_usd: number;
  total_penalty_usd: number;
  criminal_risk_flag: boolean;
  mitigation_options: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token") ?? localStorage.getItem("access_token") ?? localStorage.getItem("jwt_token");
}

function fmtUSD(val: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(val);
}

// ---------------------------------------------------------------------------
// Shared styles (dark theme)
// ---------------------------------------------------------------------------

const S = {
  input:
    "w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500 text-sm",
  label: "block text-sm font-medium text-gray-300 mb-1",
  labelSm: "block text-xs text-gray-500 mb-1",
  btn: "px-6 py-2.5 rounded-md bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold transition-colors text-sm",
  card: "bg-gray-800 rounded-lg p-4 border border-gray-700",
  errorBox:
    "p-4 rounded-md bg-red-900/40 border border-red-700 text-red-300 text-sm",
};

// ---------------------------------------------------------------------------
// Tab 1: Filing Requirement
// ---------------------------------------------------------------------------

function FilingRequirementTab() {
  const [form, setForm] = useState<FilingRequirementRequest>({
    ownership_type: "direct_fde",
    ownership_percentage: 100,
    is_us_person: true,
    entity_country: "",
    tax_year: new Date().getFullYear() - 1,
  });
  const [result, setResult] = useState<FilingRequirementResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      if (!token) throw new Error("Not authenticated. Please log in.");
      const resp = await fetch(`${API_BASE}/api/v1/form8858/filing-requirement`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className={S.card}>
        <h3 className="text-base font-semibold text-white mb-4">
          Form 8858 Filing Requirement Checker
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={S.label}>Ownership Type</label>
              <select
                className={S.input}
                value={form.ownership_type}
                onChange={(e) =>
                  setForm({ ...form, ownership_type: e.target.value as FilingRequirementRequest["ownership_type"] })
                }
              >
                <option value="direct_fde">Direct FDE</option>
                <option value="indirect_fde">Indirect FDE</option>
                <option value="foreign_branch">Foreign Branch</option>
                <option value="cfc_fde">CFC-owned FDE</option>
              </select>
            </div>
            <div>
              <label className={S.label}>Ownership Percentage (%)</label>
              <input
                type="number"
                min={0}
                max={100}
                step={0.1}
                className={S.input}
                value={form.ownership_percentage}
                onChange={(e) =>
                  setForm({ ...form, ownership_percentage: parseFloat(e.target.value) || 0 })
                }
              />
            </div>
            <div>
              <label className={S.label}>Entity Country</label>
              <input
                type="text"
                className={S.input}
                placeholder="e.g., Germany"
                value={form.entity_country}
                onChange={(e) => setForm({ ...form, entity_country: e.target.value })}
              />
            </div>
            <div>
              <label className={S.label}>Tax Year</label>
              <input
                type="number"
                min={2000}
                max={2099}
                className={S.input}
                value={form.tax_year}
                onChange={(e) =>
                  setForm({ ...form, tax_year: parseInt(e.target.value) || 2024 })
                }
              />
            </div>
            <div className="flex items-center gap-3">
              <input
                id="is_us_person"
                type="checkbox"
                className="w-4 h-4 accent-blue-500"
                checked={form.is_us_person}
                onChange={(e) => setForm({ ...form, is_us_person: e.target.checked })}
              />
              <label htmlFor="is_us_person" className={S.label}>
                Is U.S. Person
              </label>
            </div>
          </div>
          <button type="submit" className={S.btn} disabled={loading}>
            {loading ? "Checking…" : "Check Filing Requirement"}
          </button>
        </form>
      </div>

      {error && <div className={S.errorBox}>{error}</div>}

      {result && (
        <div className={S.card}>
          <div
            className={`text-lg font-bold mb-3 ${
              result.must_file ? "text-red-400" : "text-green-400"
            }`}
          >
            {result.must_file ? "⚠ Form 8858 REQUIRED" : "✓ Form 8858 Not Required"}
          </div>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-gray-400 font-medium">Reason: </span>
              <span className="text-gray-200">{result.reason}</span>
            </div>
            <div>
              <span className="text-gray-400 font-medium">Due Date: </span>
              <span className="text-gray-200">{result.form_due_date}</span>
            </div>
            <div>
              <span className="text-gray-400 font-medium">Penalty if Not Filed: </span>
              <span className="text-yellow-400 font-semibold">
                {fmtUSD(result.penalty_if_not_filed_usd)}
              </span>
            </div>
            <div>
              <span className="text-gray-400 font-medium">Filing Instructions: </span>
              <span className="text-gray-200">{result.filing_instructions}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 2: Income Summary
// ---------------------------------------------------------------------------

function IncomeSummaryTab() {
  const [form, setForm] = useState<IncomeSummaryRequest>({
    gross_receipts_usd: 0,
    cost_of_goods_sold_usd: 0,
    operating_expenses_usd: 0,
    depreciation_usd: 0,
    other_income_usd: 0,
    other_deductions_usd: 0,
  });
  const [result, setResult] = useState<IncomeSummaryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const numField = (
    label: string,
    key: keyof IncomeSummaryRequest
  ) => (
    <div>
      <label className={S.label}>{label} (USD)</label>
      <input
        type="number"
        min={0}
        step={0.01}
        className={S.input}
        value={form[key]}
        onChange={(e) =>
          setForm({ ...form, [key]: parseFloat(e.target.value) || 0 })
        }
      />
    </div>
  );

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      if (!token) throw new Error("Not authenticated. Please log in.");
      const resp = await fetch(`${API_BASE}/api/v1/form8858/income-summary`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className={S.card}>
        <h3 className="text-base font-semibold text-white mb-4">
          FDE Income Summary (Form 8858 Schedule C)
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {numField("Gross Receipts", "gross_receipts_usd")}
            {numField("Cost of Goods Sold", "cost_of_goods_sold_usd")}
            {numField("Operating Expenses", "operating_expenses_usd")}
            {numField("Depreciation", "depreciation_usd")}
            {numField("Other Income", "other_income_usd")}
            {numField("Other Deductions", "other_deductions_usd")}
          </div>
          <button type="submit" className={S.btn} disabled={loading}>
            {loading ? "Calculating…" : "Calculate Income Summary"}
          </button>
        </form>
      </div>

      {error && <div className={S.errorBox}>{error}</div>}

      {result && (
        <div className={S.card}>
          <h4 className="text-base font-semibold text-white mb-4">Income Summary Results</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-700 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Gross Income</div>
              <div className="text-lg font-bold text-blue-300">
                {fmtUSD(result.gross_income_usd)}
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Total Deductions</div>
              <div className="text-lg font-bold text-orange-300">
                {fmtUSD(result.total_deductions_usd)}
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Net Income / Loss</div>
              <div
                className={`text-lg font-bold ${
                  result.is_profitable ? "text-green-400" : "text-red-400"
                }`}
              >
                {fmtUSD(result.net_income_loss_usd)}
              </div>
            </div>
          </div>
          <div className="text-sm">
            <div
              className={`mb-2 font-semibold ${
                result.is_profitable ? "text-green-400" : "text-red-400"
              }`}
            >
              {result.is_profitable ? "✓ Profitable" : "✗ Loss Position"}
            </div>
            <p className="text-gray-300">{result.us_tax_implications}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 3: Penalty Calculator
// ---------------------------------------------------------------------------

function PenaltyCalculatorTab() {
  const [form, setForm] = useState<PenaltyRequest>({
    years_not_filed: 1,
    continued_failure_periods: 0,
  });
  const [result, setResult] = useState<PenaltyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      if (!token) throw new Error("Not authenticated. Please log in.");
      const resp = await fetch(`${API_BASE}/api/v1/form8858/penalty-calculator`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className={S.card}>
        <h3 className="text-base font-semibold text-white mb-4">
          IRC §6038 Penalty Calculator
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={S.label}>Years Not Filed (1–10)</label>
              <input
                type="number"
                min={1}
                max={10}
                className={S.input}
                value={form.years_not_filed}
                onChange={(e) =>
                  setForm({ ...form, years_not_filed: parseInt(e.target.value) || 1 })
                }
              />
            </div>
            <div>
              <label className={S.label}>
                Continued Failure Periods (0–5)
              </label>
              <input
                type="number"
                min={0}
                max={5}
                className={S.input}
                value={form.continued_failure_periods}
                onChange={(e) =>
                  setForm({
                    ...form,
                    continued_failure_periods: parseInt(e.target.value) || 0,
                  })
                }
              />
              <p className={S.labelSm}>
                Each period = 30 days × $10,000 (max 5 per year)
              </p>
            </div>
          </div>
          <button type="submit" className={S.btn} disabled={loading}>
            {loading ? "Calculating…" : "Calculate Penalties"}
          </button>
        </form>
      </div>

      {error && <div className={S.errorBox}>{error}</div>}

      {result && (
        <div className={S.card}>
          <h4 className="text-base font-semibold text-white mb-4">Penalty Estimate</h4>

          {result.criminal_risk_flag && (
            <div className="mb-4 p-3 rounded-md bg-red-900/60 border border-red-600 text-red-200 text-sm font-semibold">
              ⚠️ CRIMINAL RISK: Total penalties exceed $50,000. Immediate legal counsel strongly advised.
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-700 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Base Penalty</div>
              <div className="text-lg font-bold text-yellow-300">
                {fmtUSD(result.base_penalty_usd)}
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Continuation Penalty</div>
              <div className="text-lg font-bold text-orange-400">
                {fmtUSD(result.continuation_penalty_usd)}
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Total Penalty</div>
              <div className="text-2xl font-bold text-red-400">
                {fmtUSD(result.total_penalty_usd)}
              </div>
            </div>
          </div>

          <div>
            <h5 className="text-sm font-semibold text-gray-300 mb-2">
              Mitigation Options:
            </h5>
            <ul className="space-y-1">
              {result.mitigation_options.map((opt, i) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-blue-400">•</span>
                  <span>{opt}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type TabName = "Filing Requirement" | "Income Summary" | "Penalty Calculator";
const TABS: TabName[] = ["Filing Requirement", "Income Summary", "Penalty Calculator"];

export default function Form8858Page() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabName>("Filing Requirement");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/auth/login");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="mx-auto max-w-5xl px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Form 8858</h1>
            <p className="text-xs text-gray-400">
              Foreign Disregarded Entities &amp; Foreign Branches
            </p>
          </div>
          <Link
            href="/dashboard"
            className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            ← Dashboard
          </Link>
        </div>
      </header>

      {/* Info Banner */}
      <div className="bg-blue-900/30 border-b border-blue-800/50">
        <div className="mx-auto max-w-5xl px-4 py-3">
          <p className="text-xs text-blue-300">
            <strong>IRC §6038:</strong> U.S. persons who own or operate Foreign Disregarded Entities (FDEs)
            or Foreign Branches (FBs) must file Form 8858 annually. Failure to file carries a{" "}
            <strong>$10,000 per-year penalty</strong> plus continuation penalties up to $50,000/year.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="mx-auto max-w-5xl px-4 pt-6">
        <div className="flex gap-1 bg-gray-800 rounded-lg p-1 mb-6 w-fit">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-700"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="pb-12">
          {activeTab === "Filing Requirement" && <FilingRequirementTab />}
          {activeTab === "Income Summary" && <IncomeSummaryTab />}
          {activeTab === "Penalty Calculator" && <PenaltyCalculatorTab />}
        </div>
      </div>
    </div>
  );
}
