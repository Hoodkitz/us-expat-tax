"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiForm8840Calculate,
  apiForm8840Overview,
  TenantOut,
  Form8840Result,
  Form8840Overview,
} from "@/lib/api";

// -----------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------

const EXEMPT_CATEGORIES = [
  "F visa — Student (Academic)",
  "J visa — Exchange Visitor",
  "M visa — Vocational Student",
  "Q visa — Cultural Exchange",
  "Teacher or Trainee",
  "Professional Athlete (charitable event)",
];

// -----------------------------------------------------------------------
// Main Page Component
// -----------------------------------------------------------------------

export default function Form8840Page() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [authError, setAuthError] = useState(false);
  const [activeTab, setActiveTab] = useState<"calculate" | "overview">("calculate");

  // Form state
  const [daysInUs, setDaysInUs] = useState("100");
  const [taxYear, setTaxYear] = useState("2024");
  const [closerConnection, setCloserConnection] = useState(true);
  const [exemptIndividual, setExemptIndividual] = useState(false);

  // Results
  const [result, setResult] = useState<Form8840Result | null>(null);
  const [overview, setOverview] = useState<Form8840Overview | null>(null);
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
    apiForm8840Overview()
      .then(setOverview)
      .catch(() => {
        // Overview is non-critical
      });
  }, []);

  // ---- Submit handler ----
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const res = await apiForm8840Calculate({
        days_in_us: parseInt(daysInUs, 10),
        tax_year: parseInt(taxYear, 10),
        closer_connection: closerConnection,
        exempt_individual: exemptIndividual,
      });
      setResult(res);
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
            href="/form8843"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Form 8843
          </Link>
          <Link
            href="/form8840"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Form 8840
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
            Form 8840: Closer Connection Exception
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Prüfen Sie, ob Sie durch eine „Closer Connection" an die USA gebunden sind
            und als Resident Alien gelten — auch wenn Sie weniger als 183 Tage in den
            USA waren.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200">
          <button
            onClick={() => setActiveTab("calculate")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "calculate"
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Berechnung
          </button>
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "overview"
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Übersicht
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* ---- Calculate Tab ---- */}
        {activeTab === "calculate" && (
          <div className="space-y-6">
            <section className="no-print rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-800 mb-6">
                Closer Connection Exception prüfen
              </h2>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label htmlFor="days_in_us" className="block text-sm font-medium text-gray-700 mb-1">
                      Tage in den USA <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="days_in_us"
                      type="number"
                      min="0"
                      max="366"
                      required
                      value={daysInUs}
                      onChange={(e) => setDaysInUs(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="tax_year" className="block text-sm font-medium text-gray-700 mb-1">
                      Steuerjahr <span className="text-red-500">*</span>
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

                <div className="space-y-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={closerConnection}
                      onChange={(e) => setCloserConnection(e.target.checked)}
                      className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="text-sm text-gray-700">
                      <strong>Closer Connection</strong> — Ich habe eine engere Verbindung
                      zu den USA als zu einem anderen Land
                    </span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exemptIndividual}
                      onChange={(e) => setExemptIndividual(e.target.checked)}
                      className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="text-sm text-gray-700">
                      <strong>Exempt Individual</strong> — Ich gelte als befreite Person
                      (z.B. Student, Lehrer, Auszubildender)
                    </span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
                >
                  {loading ? "Berechnung läuft …" : "Closer Connection prüfen"}
                </button>
              </form>
            </section>

            {/* Result */}
            {result && (
              <div className="print-section space-y-6">
                <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="text-2xl">
                      {result.resident_alien ? "⚠️" : "✅"}
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-gray-800">
                        {result.resident_alien
                          ? "Sie gelten als U.S. Resident Alien"
                          : "Sie gelten NICHT als U.S. Resident Alien"}
                      </h2>
                    </div>
                  </div>

                  <div className="grid gap-5 sm:grid-cols-2">
                    <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                      <h3 className="font-semibold text-gray-800 text-sm mb-3">
                        Details
                      </h3>
                      <dl className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Resident Alien</dt>
                          <dd className="font-medium text-gray-800">
                            {result.resident_alien ? "Ja" : "Nein"}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Tage in den USA</dt>
                          <dd className="font-medium text-gray-800">
                            {result.days_in_us}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Closer Connection</dt>
                          <dd className="font-medium text-gray-800">
                            {result.closer_connection ? "Ja" : "Nein"}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Exempt Individual</dt>
                          <dd className="font-medium text-gray-800">
                            {result.exempt_individual ? "Ja" : "Nein"}
                          </dd>
                        </div>
                      </dl>
                    </div>

                    <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                      <h3 className="font-semibold text-gray-800 text-sm mb-3">
                        Erklärung
                      </h3>
                      <p className="text-sm text-gray-600">{result.explanation}</p>
                    </div>
                  </div>
                </section>
              </div>
            )}
          </div>
        )}

        {/* ---- Overview Tab ---- */}
        {activeTab === "overview" && overview && (
          <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">
              Übersicht: Form 8840
            </h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Zweck</h3>
                <p className="text-sm text-gray-600">{overview.purpose}</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Wer muss einreichen?
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  {overview.who_must_file.map((item, i) => (
                    <li key={i}>• {item}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Schlüsselregeln
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  {overview.key_rules.map((rule, i) => (
                    <li key={i}>• {rule}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Faktoren für eine „Closer Connection"
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  {overview.closer_connection_factors.map((factor, i) => (
                    <li key={i}>• {factor}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Exempt Individual — Kategorien
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  {overview.exempt_individual_categories.map((cat, i) => (
                    <li key={i}>• {cat}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Frist</h3>
                <p className="text-sm text-gray-600">{overview.filing_deadline}</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  IRS Referenz
                </h3>
                <a
                  href={overview.irs_reference}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-brand-600 hover:text-brand-800 underline"
                >
                  {overview.irs_reference}
                </a>
              </div>
            </div>
          </section>
        )}

        {/* Disclaimer */}
        <p className="text-xs italic text-gray-500">
          Hinweis: Diese Berechnung ist eine Schätzung. Bitte konsultieren Sie
          einen qualifizierten Steuerberater.
        </p>
      </main>
    </div>
  );
}
