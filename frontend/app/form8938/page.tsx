"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiForm8938FilingRequirement,
  apiForm8938PenaltyCalculator,
  apiForm8938Overview,
  TenantOut,
  ForeignAccount8938,
  FilingRequirement8938Result,
  PenaltyResult8938,
  Form8938Overview,
} from "@/lib/api";

// -----------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------

const ACCOUNT_TYPES = [
  { value: "bank_account", label: "Bank Account (checking, savings, time deposits)" },
  { value: "brokerage_account", label: "Brokerage Account (stocks, bonds, securities)" },
  { value: "mutual_fund", label: "Mutual Fund / ETF" },
  { value: "life_insurance", label: "Life Insurance Policy (with cash value)" },
  { value: "pension_fund", label: "Pension Fund / Retirement Account" },
  { value: "trust", label: "Foreign Trust / Estate" },
  { value: "other", label: "Other Financial Instrument" },
];

const FILING_STATUSES = [
  { value: "single", label: "Single" },
  { value: "mfj", label: "Married Filing Jointly (MFJ)" },
  { value: "mfs", label: "Married Filing Separately (MFS)" },
  { value: "hoh", label: "Head of Household (HOH)" },
];

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function fmtUSD(val: number | undefined): string {
  if (val === undefined || val === null) return "–";
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(val);
}

// -----------------------------------------------------------------------
// Main Page Component
// -----------------------------------------------------------------------

export default function Form8938Page() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [authError, setAuthError] = useState(false);

  // Form state
  const [filingStatus, setFilingStatus] = useState<"single" | "mfj" | "mfs" | "hoh">("single");
  const [taxYear, setTaxYear] = useState("2024");
  const [accounts, setAccounts] = useState<ForeignAccount8938[]>([
    { account_name: "", account_type: "bank_account", country: "", max_value_usd: 0 },
  ]);
  const [daysUnreported, setDaysUnreported] = useState("0");
  const [isWillful, setIsWillful] = useState(false);

  // Result state
  const [filingResult, setFilingResult] = useState<FilingRequirement8938Result | null>(null);
  const [penaltyResult, setPenaltyResult] = useState<PenaltyResult8938 | null>(null);
  const [overview, setOverview] = useState<Form8938Overview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---- Auth guard ----
  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }
    apiMe()
      .then(setTenant)
      .catch(() => {
        localStorage.removeItem("jwt_token");
        setAuthError(true);
        router.replace("/auth/login");
      });
  }, [router]);

  // ---- Load overview on mount ----
  useEffect(() => {
    apiForm8938Overview()
      .then(setOverview)
      .catch(() => {
        // Overview is non-critical
      });
  }, []);

  // ---- Account management ----
  function addAccount() {
    setAccounts([
      ...accounts,
      { account_name: "", account_type: "bank_account", country: "", max_value_usd: 0 },
    ]);
  }

  function removeAccount(index: number) {
    setAccounts(accounts.filter((_, i) => i !== index));
  }

  function updateAccount(index: number, field: keyof ForeignAccount8938, value: string | number) {
    const updated = [...accounts];
    updated[index] = { ...updated[index], [field]: value };
    setAccounts(updated);
  }

  // ---- Form submission ----
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setFilingResult(null);
    setPenaltyResult(null);
    setLoading(true);

    try {
      const payload = {
        filing_status: filingStatus,
        accounts: accounts.filter((a) => a.account_name && a.country),
        tax_year: parseInt(taxYear, 10),
      };

      // Check filing requirement
      const filingRes = await apiForm8938FilingRequirement(payload);
      setFilingResult(filingRes);

      // Calculate penalties
      const penaltyRes = await apiForm8938PenaltyCalculator({
        ...payload,
        days_unreported: parseInt(daysUnreported, 10),
        is_willful: isWillful,
      });
      setPenaltyResult(penaltyRes);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  if (authError) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="no-print bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <span className="font-extrabold text-brand-800 text-lg">
          🇺🇸 US Expat Tax
        </span>
        <div className="flex items-center gap-4">
          {tenant && (
            <span className="text-sm text-gray-600 hidden sm:block">
              <strong>{tenant.tenant_name}</strong>{" "}
              <span className="text-gray-400">({tenant.email})</span>
            </span>
          )}
          <Link
            href="/dashboard"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Dashboard
          </Link>
          <Link
            href="/fbar"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            FBAR
          </Link>
          <Link
            href="/form8621"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Form 8621
          </Link>
          <Link
            href="/auth/logout"
            className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Abmelden
          </Link>
        </div>
      </nav>

      <main className="mx-auto max-w-4xl px-4 py-10 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            Form 8938: FATCA Foreign Financial Asset Reporting
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Prüfen Sie, ob Sie ausländische Finanzkonten melden müssen, und berechnen Sie mögliche Strafen.
          </p>
        </div>

        {/* Overview */}
        {overview && (
          <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">
              Übersicht: Form 8938 FATCA
            </h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Meldepflicht</h3>
                <p className="text-sm text-gray-600">{overview.filing_requirement}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Schwellenwerte</h3>
                <div className="grid gap-2 sm:grid-cols-2">
                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-500">Single / MFS / HOH (Jahresende)</p>
                    <p className="text-lg font-semibold text-gray-800">
                      {fmtUSD(overview.thresholds.single_year_end)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-500">MFJ (Jahresende)</p>
                    <p className="text-lg font-semibold text-gray-800">
                      {fmtUSD(overview.thresholds.mfj_year_end)}
                    </p>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Strafen</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Nichtmeldung: {fmtUSD(overview.penalties.failure_to_file)} pro Jahr</li>
                  <li>• Fortgesetzte Nichtmeldung: {fmtUSD(overview.penalties.continued_failure_per_30_days)} pro 30-Tage-Zeitraum (max. {fmtUSD(overview.penalties.continued_failure_max)})</li>
                  <li>• Vorsätzliche Nichtmeldung: {fmtUSD(overview.penalties.willful_minimum)} oder 50% des Kontowerts</li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Empfehlung</h3>
                <p className="text-sm text-gray-600">{overview.recommendation}</p>
              </div>
            </div>
          </section>
        )}

        {/* Input Form */}
        <section className="no-print rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800 mb-6">
            Meldepflicht prüfen
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Filing Status & Tax Year */}
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="filing_status"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Steuerstatus (Filing Status){" "}
                  <span className="text-red-500">*</span>
                </label>
                <select
                  id="filing_status"
                  value={filingStatus}
                  onChange={(e) => setFilingStatus(e.target.value as "single" | "mfj" | "mfs" | "hoh")}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  {FILING_STATUSES.map((fs) => (
                    <option key={fs.value} value={fs.value}>
                      {fs.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label
                  htmlFor="tax_year"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Steuerjahr{" "}
                  <span className="text-red-500">*</span>
                </label>
                <input
                  id="tax_year"
                  type="number"
                  min="2000"
                  max="2099"
                  required
                  value={taxYear}
                  onChange={(e) => setTaxYear(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>
            </div>

            {/* Accounts */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Ausländische Finanzkonten{" "}
                  <span className="text-red-500">*</span>
                </label>
                <button
                  type="button"
                  onClick={addAccount}
                  className="rounded-lg border border-brand-300 px-3 py-1 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
                >
                  + Konto hinzufügen
                </button>
              </div>

              <div className="space-y-4">
                {accounts.map((account, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-600">
                        Konto {index + 1}
                      </span>
                      {accounts.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeAccount(index)}
                          className="text-sm text-red-600 hover:text-red-800"
                        >
                          Entfernen
                        </button>
                      )}
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">
                          Kontoname / Beschreibung
                        </label>
                        <input
                          type="text"
                          value={account.account_name}
                          onChange={(e) =>
                            updateAccount(index, "account_name", e.target.value)
                          }
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                          placeholder="z. B. Deutsche Bank Savings"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">
                          Kontotyp
                        </label>
                        <select
                          value={account.account_type}
                          onChange={(e) =>
                            updateAccount(index, "account_type", e.target.value)
                          }
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                        >
                          {ACCOUNT_TYPES.map((at) => (
                            <option key={at.value} value={at.value}>
                              {at.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">
                          Land
                        </label>
                        <input
                          type="text"
                          value={account.country}
                          onChange={(e) =>
                            updateAccount(index, "country", e.target.value)
                          }
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                          placeholder="z. B. DE"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">
                          Höchstwert im Steuerjahr (USD)
                        </label>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={account.max_value_usd}
                          onChange={(e) =>
                            updateAccount(index, "max_value_usd", parseFloat(e.target.value) || 0)
                          }
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                          placeholder="z. B. 15000"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Penalty Options */}
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="days_unreported"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Tage nach IRS-Meldung (fortgesetzte Nichtmeldung)
                </label>
                <input
                  id="days_unreported"
                  type="number"
                  min="0"
                  value={daysUnreported}
                  onChange={(e) => setDaysUnreported(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-gray-400">
                  Anzahl der Tage, die die Nichtmeldung nach einer IRS-Meldung andauert
                </p>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isWillful}
                    onChange={(e) => setIsWillful(e.target.checked)}
                    className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span className="text-sm text-gray-700">
                    Vorsätzliche Nichtmeldung
                  </span>
                </label>
              </div>
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
            >
              {loading ? "Berechnung läuft …" : "Meldepflicht & Strafen berechnen"}
            </button>
          </form>
        </section>

        {/* Results */}
        {(filingResult || penaltyResult) && (
          <div className="print-section space-y-6">
            {/* Filing Requirement Result */}
            {filingResult && (
              <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <div className="text-2xl">
                    {filingResult.filing_required ? "⚠️" : "✅"}
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-800">
                      {filingResult.filing_required
                        ? "Form 8938 Meldepflicht besteht"
                        : "Keine Form 8938 Meldepflicht"}
                    </h2>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {filingResult.recommendation}
                    </p>
                  </div>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                    <h3 className="font-semibold text-gray-800 text-sm mb-3">
                      Berechnung
                    </h3>
                    <dl className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <dt className="text-gray-500">Gesamtwert</dt>
                        <dd className="font-medium text-gray-800">
                          {fmtUSD(filingResult.total_value_usd)}
                        </dd>
                      </div>
                      <div className="flex justify-between text-sm">
                        <dt className="text-gray-500">Schwellenwert</dt>
                        <dd className="font-medium text-gray-800">
                          {fmtUSD(filingResult.threshold_usd)}
                        </dd>
                      </div>
                      <div className="flex justify-between text-sm">
                        <dt className="text-gray-500">Strafe bei Nichtmeldung</dt>
                        <dd className="font-medium text-gray-800">
                          {fmtUSD(filingResult.penalty_if_not_filed)}
                        </dd>
                      </div>
                    </dl>
                  </div>

                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                    <h3 className="font-semibold text-gray-800 text-sm mb-3">
                      Gründe
                    </h3>
                    <ul className="space-y-1">
                      {filingResult.reasons.map((reason, i) => (
                        <li key={i} className="text-sm text-gray-600">
                          • {reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            )}

            {/* Penalty Result */}
            {penaltyResult && (
              <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">
                  Strafe Berechnung
                </h2>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                    <h3 className="font-semibold text-gray-800 text-sm mb-3">
                      Strafe-Aufschlüsselung
                    </h3>
                    <dl className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <dt className="text-gray-500">Basisstrafe</dt>
                        <dd className="font-medium text-gray-800">
                          {fmtUSD(penaltyResult.base_penalty)}
                        </dd>
                      </div>
                      <div className="flex justify-between text-sm">
                        <dt className="text-gray-500">Fortgesetzte Nichtmeldung</dt>
                        <dd className="font-medium text-gray-800">
                          {fmtUSD(penaltyResult.continued_failure_penalty)}
                        </dd>
                      </div>
                      <div className="flex justify-between text-sm">
                        <dt className="text-gray-500">Vorsätzliche Strafe</dt>
                        <dd className="font-medium text-gray-800">
                          {fmtUSD(penaltyResult.willful_penalty)}
                        </dd>
                      </div>
                      <div className="flex justify-between text-sm border-t border-gray-200 pt-2 mt-2">
                        <dt className="font-semibold text-gray-700">Gesamtstrafe</dt>
                        <dd className="font-bold text-red-600">
                          {fmtUSD(penaltyResult.total_penalty)}
                        </dd>
                      </div>
                    </dl>
                  </div>

                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                    <h3 className="font-semibold text-gray-800 text-sm mb-3">
                      Erklärung
                    </h3>
                    <p className="text-sm text-gray-600">{penaltyResult.explanation}</p>
                  </div>
                </div>
              </section>
            )}

            {/* Disclaimer */}
            <p className="text-xs italic text-gray-500">
              Hinweis: Diese Berechnung ist eine Schätzung. Bitte konsultieren Sie
              einen qualifizierten Steuerberater.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
