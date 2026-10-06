"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FTCCalculateRequest {
  foreign_taxes_paid: number;
  foreign_income: number;
  total_income: number;
  us_tax_before_credit: number;
  income_category: string;
  tax_year: number;
}

interface FTCResult {
  ftc_limitation: number;
  allowable_ftc: number;
  excess_credit: number;
  us_tax_after_credit: number;
  effective_rate: number;
  carryforward_years: number;
  carryback_years: number;
  recommendation: string;
  income_category_explanation: string;
}

interface FeieVsFtcRequest {
  foreign_income: number;
  foreign_taxes_paid: number;
  total_us_income: number;
  tax_year: number;
}

interface StrategyResult {
  strategy: string;
  excluded_or_credited: number;
  us_tax_owed: number;
  net_tax_saving: number;
  description: string;
}

interface FeieVsFtcResult {
  feie: StrategyResult;
  ftc: StrategyResult;
  recommended_strategy: string;
  recommendation_detail: string;
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

function fmtPct(val: number): string {
  return `${val.toFixed(2)}%`;
}

// ---------------------------------------------------------------------------
// FTC Rechner Tab
// ---------------------------------------------------------------------------

function FTCRechner() {
  const [form, setForm] = useState<FTCCalculateRequest>({
    foreign_taxes_paid: 15000,
    foreign_income: 80000,
    total_income: 100000,
    us_tax_before_credit: 18000,
    income_category: "general",
    tax_year: 2024,
  });
  const [result, setResult] = useState<FTCResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]:
        name === "income_category" ? value : parseFloat(value) || 0,
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    const token = getToken();
    try {
      const resp = await fetch(`${API_BASE}/api/v1/form1116/calculate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(form),
      });
      if (!resp.ok) {
        const detail = await resp.json().catch(() => ({}));
        throw new Error(detail.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Form */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-100">
          Form 1116 Eingaben
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Steuerjahr
              </label>
              <input
                type="number"
                name="tax_year"
                value={form.tax_year}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
                min={2000}
                max={2099}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Income Category
              </label>
              <select
                name="income_category"
                value={form.income_category}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
              >
                <option value="general">General</option>
                <option value="passive">Passive</option>
                <option value="section901j">Section 901(j)</option>
                <option value="certain_income_re_sanctioned_countries">
                  Sanctioned Countries
                </option>
              </select>
            </div>
          </div>

          {[
            {
              name: "foreign_taxes_paid",
              label: "Im Ausland gezahlte Steuern (USD)",
            },
            { name: "foreign_income", label: "Ausländisches Einkommen (USD)" },
            { name: "total_income", label: "Gesamteinkommen weltweit (USD)" },
            {
              name: "us_tax_before_credit",
              label: "US-Steuer vor Credit (USD)",
            },
          ].map(({ name, label }) => (
            <div key={name}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {label}
              </label>
              <input
                type="number"
                name={name}
                value={form[name as keyof FTCCalculateRequest]}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
                min={0}
                step="0.01"
              />
            </div>
          ))}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Berechnung…" : "FTC Berechnen"}
          </button>

          {error && (
            <p className="text-red-600 dark:text-red-400 text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
              {error}
            </p>
          )}
        </form>
      </div>

      {/* Results */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-100">
          Ergebnis
        </h2>
        {!result && !loading && (
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Füllen Sie das Formular aus und klicken Sie auf &quot;FTC Berechnen&quot;.
          </p>
        )}
        {result && (
          <div className="space-y-4">
            {/* Key metrics */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "FTC Limitation", value: fmtUSD(result.ftc_limitation) },
                {
                  label: "Anrechenbarer Credit",
                  value: fmtUSD(result.allowable_ftc),
                  highlight: true,
                },
                { label: "Überschuss-Credit", value: fmtUSD(result.excess_credit) },
                {
                  label: "US-Steuer nach Credit",
                  value: fmtUSD(result.us_tax_after_credit),
                  highlight: true,
                },
                { label: "Effektiver Steuersatz", value: fmtPct(result.effective_rate) },
                { label: "Carryforward / Carryback", value: `${result.carryforward_years}J / ${result.carryback_years}J` },
              ].map(({ label, value, highlight }) => (
                <div
                  key={label}
                  className={`rounded-lg p-3 ${
                    highlight
                      ? "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700"
                      : "bg-gray-50 dark:bg-gray-700/50"
                  }`}
                >
                  <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                  <p
                    className={`text-base font-semibold ${
                      highlight
                        ? "text-blue-700 dark:text-blue-300"
                        : "text-gray-800 dark:text-gray-100"
                    }`}
                  >
                    {value}
                  </p>
                </div>
              ))}
            </div>

            {/* Recommendation */}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4">
              <p className="text-sm text-green-800 dark:text-green-200">
                {result.recommendation}
              </p>
            </div>

            {/* Explanation */}
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Income Category
              </p>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {result.income_category_explanation}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// FEIE vs FTC Tab
// ---------------------------------------------------------------------------

function FeieVsFtcVergleich() {
  const [form, setForm] = useState<FeieVsFtcRequest>({
    foreign_income: 100000,
    foreign_taxes_paid: 5000,
    total_us_income: 120000,
    tax_year: 2024,
  });
  const [result, setResult] = useState<FeieVsFtcResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: parseFloat(value) || 0 }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const resp = await fetch(
        `${API_BASE}/api/v1/form1116/feie-vs-ftc-compare`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        }
      );
      if (!resp.ok) {
        const detail = await resp.json().catch(() => ({}));
        throw new Error(detail.detail ?? `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Form */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-100">
          Eingaben für den Vergleich
        </h2>
        <form
          onSubmit={handleSubmit}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {[
            { name: "tax_year", label: "Steuerjahr", min: 2000, max: 2099, step: 1 },
            { name: "foreign_income", label: "Ausländisches Einkommen (USD)", min: 0, step: 0.01 },
            { name: "foreign_taxes_paid", label: "Im Ausland gezahlte Steuern (USD)", min: 0, step: 0.01 },
            { name: "total_us_income", label: "Gesamteinkommen (USD)", min: 0.01, step: 0.01 },
          ].map(({ name, label, min, max, step }) => (
            <div key={name}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {label}
              </label>
              <input
                type="number"
                name={name}
                value={form[name as keyof FeieVsFtcRequest]}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
                min={min}
                max={max}
                step={step}
              />
            </div>
          ))}
          <div className="sm:col-span-2 lg:col-span-4 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-8 rounded-lg transition-colors disabled:opacity-50"
            >
              {loading ? "Berechnung…" : "Vergleichen"}
            </button>
          </div>
          {error && (
            <div className="sm:col-span-2 lg:col-span-4">
              <p className="text-red-600 dark:text-red-400 text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                {error}
              </p>
            </div>
          )}
        </form>
      </div>

      {/* Side-by-side results */}
      {result && (
        <div className="space-y-4">
          {/* Recommendation banner */}
          <div
            className={`rounded-xl p-4 border ${
              result.recommended_strategy.includes("FEIE")
                ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-700"
                : "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700"
            }`}
          >
            <p className="font-semibold text-gray-800 dark:text-gray-100">
              ✅ Empfehlung: {result.recommended_strategy}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
              {result.recommendation_detail}
            </p>
          </div>

          {/* Side-by-side table */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[result.feie, result.ftc].map((strategy) => {
              const isRecommended =
                strategy.strategy === result.recommended_strategy;
              return (
                <div
                  key={strategy.strategy}
                  className={`rounded-xl shadow p-5 border-2 ${
                    isRecommended
                      ? "border-blue-400 dark:border-blue-500 bg-white dark:bg-gray-800"
                      : "border-transparent bg-white dark:bg-gray-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-800 dark:text-gray-100">
                      {strategy.strategy}
                    </h3>
                    {isRecommended && (
                      <span className="text-xs bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 px-2 py-1 rounded-full font-medium">
                        Empfohlen
                      </span>
                    )}
                  </div>
                  <table className="w-full text-sm">
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      <tr>
                        <td className="py-2 text-gray-500 dark:text-gray-400">
                          Ausschluss / Credit
                        </td>
                        <td className="py-2 text-right font-medium text-gray-800 dark:text-gray-100">
                          {fmtUSD(strategy.excluded_or_credited)}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-500 dark:text-gray-400">
                          US-Steuer
                        </td>
                        <td className="py-2 text-right font-medium text-gray-800 dark:text-gray-100">
                          {fmtUSD(strategy.us_tax_owed)}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-500 dark:text-gray-400">
                          Ersparnis
                        </td>
                        <td className="py-2 text-right font-semibold text-green-600 dark:text-green-400">
                          {fmtUSD(strategy.net_tax_saving)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <p className="mt-3 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                    {strategy.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Form1116Page() {
  const [activeTab, setActiveTab] = useState<"ftc" | "compare">("ftc");

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <Link
              href="/dashboard"
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              ← Dashboard
            </Link>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white mt-1">
              Form 1116 — Foreign Tax Credit (FTC)
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Berechnen Sie Ihren Foreign Tax Credit nach IRC §904 und vergleichen Sie
              FEIE vs. FTC.
            </p>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-6xl mx-auto px-4 pt-6">
        <div className="flex gap-1 mb-6 bg-white dark:bg-gray-800 rounded-xl p-1 shadow w-fit">
          {(
            [
              { id: "ftc", label: "FTC Rechner" },
              { id: "compare", label: "FEIE vs FTC Vergleich" },
            ] as { id: "ftc" | "compare"; label: string }[]
          ).map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === id
                  ? "bg-blue-600 text-white shadow"
                  : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {activeTab === "ftc" && <FTCRechner />}
        {activeTab === "compare" && <FeieVsFtcVergleich />}

        {/* Info box */}
        <div className="mt-8 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-5">
          <h3 className="font-semibold text-amber-800 dark:text-amber-200 mb-2">
            ⚠️ Wichtiger Hinweis
          </h3>
          <p className="text-sm text-amber-700 dark:text-amber-300">
            Diese Berechnung dient ausschließlich zu Informationszwecken. Die
            FTC-Berechnung nach Form 1116 kann komplex sein, insbesondere bei
            mehreren Income Baskets, AMT und Carryovers. Konsultieren Sie einen
            qualifizierten US-Steuerberater (CPA/Enrolled Agent) für Ihre individuelle
            Situation.
          </p>
        </div>
      </div>
      <div className="h-12" />
    </div>
  );
}
