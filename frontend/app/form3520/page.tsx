"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FilingRequirementRequest {
  received_foreign_gifts_usd: number;
  received_from_foreign_person: boolean;
  received_from_foreign_corporation_or_partnership: boolean;
  is_beneficiary_of_foreign_trust: boolean;
  transferred_to_foreign_trust: boolean;
  tax_year: number;
}

interface FilingRequirementResult {
  must_file: boolean;
  applicable_thresholds: {
    individual_foreign_gifts_usd: number;
    corp_or_partnership_gifts_usd: number;
  };
  reasons: string[];
  penalties_if_not_filed: string;
  form_due_date: string;
}

interface GiftItem {
  donor_type: "INDIVIDUAL" | "CORPORATION" | "PARTNERSHIP";
  amount_usd: number;
  date_received: string;
  donor_country: string;
}

interface GiftCalculatorResult {
  total_individual_gifts: number;
  total_corp_gifts: number;
  reporting_required: boolean;
  gifts_by_category: {
    individual: GiftItem[];
    corporation_or_partnership: GiftItem[];
  };
  penalty_exposure_usd: number;
  penalty_formula: string;
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
// Tab 1: Filing Requirement Check
// ---------------------------------------------------------------------------

function FilingRequirementTab() {
  const [form, setForm] = useState<FilingRequirementRequest>({
    received_foreign_gifts_usd: 0,
    received_from_foreign_person: false,
    received_from_foreign_corporation_or_partnership: false,
    is_beneficiary_of_foreign_trust: false,
    transferred_to_foreign_trust: false,
    tax_year: new Date().getFullYear() - 1,
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
      const resp = await fetch(`${API_BASE}/api/v1/form3520/filing-requirement`, {
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

  const checkboxField = (
    label: string,
    key: keyof FilingRequirementRequest
  ) => (
    <label className="flex items-center gap-3 cursor-pointer">
      <input
        type="checkbox"
        checked={form[key] as boolean}
        onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
        className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500"
      />
      <span className="text-sm text-gray-300">{label}</span>
    </label>
  );

  return (
    <div className="space-y-6">
      <p className="text-gray-400 text-sm">
        Answer the questions below to determine whether you must file{" "}
        <strong className="text-white">Form 3520</strong> for the selected tax
        year.
      </p>
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Gift amount */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Total foreign gifts received (USD)
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={form.received_foreign_gifts_usd}
              onChange={(e) =>
                setForm({ ...form, received_foreign_gifts_usd: parseFloat(e.target.value) || 0 })
              }
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Tax year
            </label>
            <input
              type="number"
              min={2000}
              max={2099}
              value={form.tax_year}
              onChange={(e) =>
                setForm({ ...form, tax_year: parseInt(e.target.value) || 2024 })
              }
              className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Checkboxes */}
        <div className="space-y-3 bg-gray-750 rounded-lg p-4 border border-gray-700">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">
            Applicable Situations
          </p>
          {checkboxField(
            "I received gifts from a foreign individual (non-resident alien)",
            "received_from_foreign_person"
          )}
          {checkboxField(
            "I received gifts from a foreign corporation or partnership",
            "received_from_foreign_corporation_or_partnership"
          )}
          {checkboxField(
            "I am a beneficiary of a foreign trust",
            "is_beneficiary_of_foreign_trust"
          )}
          {checkboxField(
            "I transferred money or property to a foreign trust",
            "transferred_to_foreign_trust"
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2.5 rounded-md bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold transition-colors"
        >
          {loading ? "Checking…" : "Check Filing Requirement"}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-md bg-red-900/40 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Must-file badge */}
          <div
            className={`flex items-center gap-3 p-4 rounded-lg border ${
              result.must_file
                ? "bg-red-900/30 border-red-700"
                : "bg-green-900/30 border-green-700"
            }`}
          >
            <span
              className={`text-2xl font-bold ${
                result.must_file ? "text-red-400" : "text-green-400"
              }`}
            >
              {result.must_file ? "⚠ Must File" : "✓ No Filing Required"}
            </span>
          </div>

          {/* Reasons */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
              Reasons
            </h3>
            <ul className="space-y-1.5">
              {result.reasons.map((r, i) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Thresholds */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-700 text-center">
              <p className="text-xs text-gray-500 mb-1">Individual / Estate Threshold</p>
              <p className="text-lg font-bold text-white">
                {fmtUSD(result.applicable_thresholds.individual_foreign_gifts_usd)}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 border border-gray-700 text-center">
              <p className="text-xs text-gray-500 mb-1">Corp / Partnership Threshold</p>
              <p className="text-lg font-bold text-white">
                {fmtUSD(result.applicable_thresholds.corp_or_partnership_gifts_usd)}
              </p>
            </div>
          </div>

          {/* Penalty warning */}
          {result.must_file && (
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-yellow-500 mb-1">
                Penalty Warning
              </p>
              <p className="text-sm text-yellow-200">{result.penalties_if_not_filed}</p>
              <p className="text-xs text-gray-400 mt-2">
                <strong>Due date:</strong> {result.form_due_date}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 2: Gift Calculator
// ---------------------------------------------------------------------------

const EMPTY_GIFT: GiftItem = {
  donor_type: "INDIVIDUAL",
  amount_usd: 0,
  date_received: "",
  donor_country: "",
};

function GiftCalculatorTab() {
  const [gifts, setGifts] = useState<GiftItem[]>([{ ...EMPTY_GIFT }]);
  const [taxYear, setTaxYear] = useState(new Date().getFullYear() - 1);
  const [result, setResult] = useState<GiftCalculatorResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const addGift = () => setGifts([...gifts, { ...EMPTY_GIFT }]);
  const removeGift = (i: number) => setGifts(gifts.filter((_, idx) => idx !== i));

  const updateGift = (i: number, field: keyof GiftItem, value: string | number) => {
    const updated = [...gifts];
    updated[i] = { ...updated[i], [field]: value };
    setGifts(updated);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const token = getToken();
      const resp = await fetch(`${API_BASE}/api/v1/form3520/gift-calculator`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ gifts, tax_year: taxYear }),
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
        Enter each foreign gift received. The calculator will aggregate totals
        by donor type and determine your Form 3520 reporting obligation.
      </p>
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Tax year */}
        <div className="w-48">
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Tax year
          </label>
          <input
            type="number"
            min={2000}
            max={2099}
            value={taxYear}
            onChange={(e) => setTaxYear(parseInt(e.target.value) || 2024)}
            className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Gift list */}
        <div className="space-y-3">
          {gifts.map((gift, i) => (
            <div
              key={i}
              className="bg-gray-800 rounded-lg p-4 border border-gray-700 space-y-3"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-semibold text-gray-400">Gift #{i + 1}</span>
                {gifts.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeGift(i)}
                    className="text-xs text-red-400 hover:text-red-300"
                  >
                    Remove
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Donor Type</label>
                  <select
                    value={gift.donor_type}
                    onChange={(e) => updateGift(i, "donor_type", e.target.value)}
                    className="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="INDIVIDUAL">Individual</option>
                    <option value="CORPORATION">Corporation</option>
                    <option value="PARTNERSHIP">Partnership</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Amount (USD)</label>
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    value={gift.amount_usd}
                    onChange={(e) => updateGift(i, "amount_usd", parseFloat(e.target.value) || 0)}
                    className="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Date Received</label>
                  <input
                    type="date"
                    value={gift.date_received}
                    onChange={(e) => updateGift(i, "date_received", e.target.value)}
                    className="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Donor Country</label>
                  <input
                    type="text"
                    value={gift.donor_country}
                    placeholder="DE, CH, FR…"
                    onChange={(e) => updateGift(i, "donor_country", e.target.value.toUpperCase())}
                    className="w-full px-2 py-1.5 rounded bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={addGift}
            className="px-4 py-2 rounded-md bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm font-medium transition-colors"
          >
            + Add Gift
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 rounded-md bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold transition-colors"
          >
            {loading ? "Calculating…" : "Calculate"}
          </button>
        </div>
      </form>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-md bg-red-900/40 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Summary table */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 bg-gray-900/50">
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Category</th>
                  <th className="text-right px-4 py-3 text-gray-400 font-medium">Total</th>
                  <th className="text-right px-4 py-3 text-gray-400 font-medium">Threshold</th>
                  <th className="text-right px-4 py-3 text-gray-400 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-700">
                  <td className="px-4 py-3 text-gray-300">Individual / Estate</td>
                  <td className="px-4 py-3 text-right font-mono text-white">
                    {fmtUSD(result.total_individual_gifts)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400">$100,000</td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        result.total_individual_gifts > 100_000
                          ? "bg-red-900/50 text-red-300"
                          : "bg-green-900/50 text-green-300"
                      }`}
                    >
                      {result.total_individual_gifts > 100_000 ? "Reportable" : "Below limit"}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-gray-300">Corp / Partnership</td>
                  <td className="px-4 py-3 text-right font-mono text-white">
                    {fmtUSD(result.total_corp_gifts)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400">$16,815</td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        result.total_corp_gifts > 16_815
                          ? "bg-red-900/50 text-red-300"
                          : "bg-green-900/50 text-green-300"
                      }`}
                    >
                      {result.total_corp_gifts > 16_815 ? "Reportable" : "Below limit"}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Reporting status + penalty */}
          <div
            className={`p-4 rounded-lg border ${
              result.reporting_required
                ? "bg-red-900/30 border-red-700"
                : "bg-green-900/30 border-green-700"
            }`}
          >
            <p
              className={`font-bold text-lg ${
                result.reporting_required ? "text-red-300" : "text-green-300"
              }`}
            >
              {result.reporting_required
                ? "⚠ Form 3520 reporting required"
                : "✓ No Form 3520 filing required for these gifts"}
            </p>
          </div>

          {result.reporting_required && (
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-yellow-500">
                  Maximum Penalty Exposure (25%)
                </p>
                <p className="text-xl font-bold text-yellow-300">
                  {fmtUSD(result.penalty_exposure_usd)}
                </p>
              </div>
              <p className="text-xs text-gray-400">{result.penalty_formula}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "filing" | "calculator";

export default function Form3520Page() {
  const [activeTab, setActiveTab] = useState<Tab>("filing");

  const tabs: { id: Tab; label: string }[] = [
    { id: "filing", label: "Filing Requirement Check" },
    { id: "calculator", label: "Gift Calculator" },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Form 3520 — Foreign Gift &amp; Trust Reporting</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              Determine your IRS reporting obligations for foreign gifts and trust distributions
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

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        {/* Info banner */}
        <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4 text-sm text-blue-200">
          <strong>Form 3520</strong> is filed separately from Form 1040. Individual gift threshold:{" "}
          <strong>$100,000</strong> (non-resident alien individuals &amp; foreign estates).
          Corp/Partnership threshold: <strong>$16,815</strong> (inflation-adjusted).
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          {activeTab === "filing" && <FilingRequirementTab />}
          {activeTab === "calculator" && <GiftCalculatorTab />}
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-gray-600 text-center">
          For informational purposes only. Consult a qualified US tax professional for advice.
          IRS reference:{" "}
          <a
            href="https://www.irs.gov/forms-pubs/about-form-3520"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            irs.gov/forms-pubs/about-form-3520
          </a>
        </p>
      </main>
    </div>
  );
}
