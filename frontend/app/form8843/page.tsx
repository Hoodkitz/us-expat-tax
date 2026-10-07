"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiForm8843ExemptStatus,
  apiForm8843SubstantialPresence,
  apiForm8843Overview,
  TenantOut,
  ExemptStatus8843Result,
  SubstantialPresence8843Result,
  Form8843Overview,
} from "@/lib/api";

// -----------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------

const VISA_TYPES = [
  { value: "F", label: "F — Student (Academic)" },
  { value: "J", label: "J — Exchange Visitor" },
  { value: "M", label: "M — Vocational Student" },
  { value: "Q", label: "Q — Cultural Exchange" },
  { value: "P", label: "P — Athlete/Entertainer" },
  { value: "H", label: "H — Temporary Worker" },
  { value: "L", label: "L — Intracompany Transferee" },
  { value: "O", label: "O — Extraordinary Ability" },
  { value: "B", label: "B — Business/Tourist" },
  { value: "E", label: "E — Treaty Trader" },
  { value: "other", label: "Other" },
];

// -----------------------------------------------------------------------
// Main Page Component
// -----------------------------------------------------------------------

export default function Form8843Page() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [authError, setAuthError] = useState(false);
  const [activeTab, setActiveTab] = useState<"exempt" | "spt" | "overview">("exempt");

  // Exempt Status form state
  const [usDays, setUsDays] = useState("120");
  const [foreignDays, setForeignDays] = useState("245");
  const [taxYear, setTaxYear] = useState("2024");
  const [visaType, setVisaType] = useState("F");
  const [isStudent, setIsStudent] = useState(true);
  const [isTeacher, setIsTeacher] = useState(false);
  const [isTrainee, setIsTrainee] = useState(false);
  const [isResearcher, setIsResearcher] = useState(false);

  // Substantial Presence form state
  const [spUsDays, setSpUsDays] = useState("120");
  const [spPriorYearDays, setSpPriorYearDays] = useState("60");
  const [spTwoYearsAgoDays, setSpTwoYearsAgoDays] = useState("30");
  const [spTaxYear, setSpTaxYear] = useState("2024");
  const [spIsExempt, setSpIsExempt] = useState(false);

  // Results
  const [exemptResult, setExemptResult] = useState<ExemptStatus8843Result | null>(null);
  const [spResult, setSpResult] = useState<SubstantialPresence8843Result | null>(null);
  const [overview, setOverview] = useState<Form8843Overview | null>(null);
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
    apiForm8843Overview()
      .then(setOverview)
      .catch(() => {
        // Overview is non-critical
      });
  }, []);

  // ---- Exempt Status submission ----
  async function handleExemptSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setExemptResult(null);
    setLoading(true);

    try {
      const result = await apiForm8843ExemptStatus({
        us_days_present: parseInt(usDays, 10),
        foreign_days_present: parseInt(foreignDays, 10),
        tax_year: parseInt(taxYear, 10),
        visa_type: visaType as "F" | "J" | "M" | "Q" | "P" | "H" | "L" | "O" | "B" | "E" | "other",
        is_student: isStudent,
        is_teacher: isTeacher,
        is_trainee: isTrainee,
        is_researcher: isResearcher,
      });
      setExemptResult(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  // ---- Substantial Presence submission ----
  async function handleSptSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSpResult(null);
    setLoading(true);

    try {
      const result = await apiForm8843SubstantialPresence({
        us_days_present: parseInt(spUsDays, 10),
        prior_year_us_days: parseInt(spPriorYearDays, 10),
        two_years_ago_us_days: parseInt(spTwoYearsAgoDays, 10),
        tax_year: parseInt(spTaxYear, 10),
        is_exempt: spIsExempt,
      });
      setSpResult(result);
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
            href="/form8938"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Form 8938
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
            Form 8843: Statement for Exempt Individuals
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Prüfen Sie, ob Sie als Exempt Individual gelten und berechnen Sie den Substantial Presence Test.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200">
          <button
            onClick={() => setActiveTab("exempt")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "exempt"
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Exempt Status
          </button>
          <button
            onClick={() => setActiveTab("spt")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "spt"
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Substantial Presence
          </button>
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "overview"
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Overview
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* ---- Exempt Status Tab ---- */}
        {activeTab === "exempt" && (
          <div className="space-y-6">
            <section className="no-print rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-800 mb-6">
                Exempt Individual Status prüfen
              </h2>

              <form onSubmit={handleExemptSubmit} className="space-y-6">
                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label htmlFor="us_days" className="block text-sm font-medium text-gray-700 mb-1">
                      Tage in den USA (aktuelles Jahr) <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="us_days"
                      type="number"
                      min="0"
                      max="366"
                      required
                      value={usDays}
                      onChange={(e) => setUsDays(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="foreign_days" className="block text-sm font-medium text-gray-700 mb-1">
                      Tage außerhalb der USA <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="foreign_days"
                      type="number"
                      min="0"
                      max="366"
                      required
                      value={foreignDays}
                      onChange={(e) => setForeignDays(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
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
                  <div>
                    <label htmlFor="visa_type" className="block text-sm font-medium text-gray-700 mb-1">
                      Visumtyp <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="visa_type"
                      value={visaType}
                      onChange={(e) => setVisaType(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    >
                      {VISA_TYPES.map((vt) => (
                        <option key={vt.value} value={vt.value}>
                          {vt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Rolle <span className="text-red-500">*</span>
                  </label>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isStudent}
                        onChange={(e) => setIsStudent(e.target.checked)}
                        className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                      />
                      <span className="text-sm text-gray-700">Student</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isTeacher}
                        onChange={(e) => setIsTeacher(e.target.checked)}
                        className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                      />
                      <span className="text-sm text-gray-700">Lehrer / Teacher</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isTrainee}
                        onChange={(e) => setIsTrainee(e.target.checked)}
                        className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                      />
                      <span className="text-sm text-gray-700">Auszubildender / Trainee</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isResearcher}
                        onChange={(e) => setIsResearcher(e.target.checked)}
                        className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                      />
                      <span className="text-sm text-gray-700">Forscher / Researcher</span>
                    </label>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
                >
                  {loading ? "Berechnung läuft …" : "Exempt Status prüfen"}
                </button>
              </form>
            </section>

            {/* Exempt Result */}
            {exemptResult && (
              <div className="print-section space-y-6">
                <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="text-2xl">
                      {exemptResult.exempt_status ? "✅" : "⚠️"}
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-gray-800">
                        {exemptResult.exempt_status
                          ? "Sie gelten als Exempt Individual"
                          : "Sie gelten NICHT als Exempt Individual"}
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
                          <dt className="text-gray-500">Exempt Status</dt>
                          <dd className="font-medium text-gray-800">
                            {exemptResult.exempt_status ? "Ja" : "Nein"}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Gezählte Tage</dt>
                          <dd className="font-medium text-gray-800">
                            {exemptResult.days_counted}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">SPT anwendbar</dt>
                          <dd className="font-medium text-gray-800">
                            {exemptResult.substantial_presence_test.applies ? "Ja" : "Nein"}
                          </dd>
                        </div>
                      </dl>
                    </div>

                    <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                      <h3 className="font-semibold text-gray-800 text-sm mb-3">
                        Erforderliche Formulare
                      </h3>
                      <ul className="space-y-1">
                        {exemptResult.required_forms.map((form, i) => (
                          <li key={i} className="text-sm text-gray-600">
                            • {form}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="mt-4">
                    <h3 className="font-semibold text-gray-800 text-sm mb-2">
                      Erklärung
                    </h3>
                    <p className="text-sm text-gray-600">{exemptResult.explanation}</p>
                  </div>
                </section>
              </div>
            )}
          </div>
        )}

        {/* ---- Substantial Presence Tab ---- */}
        {activeTab === "spt" && (
          <div className="space-y-6">
            <section className="no-print rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-800 mb-6">
                Substantial Presence Test berechnen
              </h2>

              <form onSubmit={handleSptSubmit} className="space-y-6">
                <div className="grid gap-5 sm:grid-cols-3">
                  <div>
                    <label htmlFor="sp_us_days" className="block text-sm font-medium text-gray-700 mb-1">
                      Tage in USA (aktuell) <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="sp_us_days"
                      type="number"
                      min="0"
                      max="366"
                      required
                      value={spUsDays}
                      onChange={(e) => setSpUsDays(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="sp_prior_year" className="block text-sm font-medium text-gray-700 mb-1">
                      Tage in USA (Vorjahr) <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="sp_prior_year"
                      type="number"
                      min="0"
                      max="366"
                      required
                      value={spPriorYearDays}
                      onChange={(e) => setSpPriorYearDays(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="sp_two_years_ago" className="block text-sm font-medium text-gray-700 mb-1">
                      Tage in USA (Vorvorjahr) <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="sp_two_years_ago"
                      type="number"
                      min="0"
                      max="366"
                      required
                      value={spTwoYearsAgoDays}
                      onChange={(e) => setSpTwoYearsAgoDays(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label htmlFor="sp_tax_year" className="block text-sm font-medium text-gray-700 mb-1">
                      Steuerjahr <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="sp_tax_year"
                      type="number"
                      min="2000"
                      max="2099"
                      required
                      value={spTaxYear}
                      onChange={(e) => setSpTaxYear(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    />
                  </div>
                  <div className="flex items-end">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={spIsExempt}
                        onChange={(e) => setSpIsExempt(e.target.checked)}
                        className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                      />
                      <span className="text-sm text-gray-700">
                        Exempt Individual (SPT nicht anwendbar)
                      </span>
                    </label>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
                >
                  {loading ? "Berechnung läuft …" : "Substantial Presence Test berechnen"}
                </button>
              </form>
            </section>

            {/* SPT Result */}
            {spResult && (
              <div className="print-section space-y-6">
                <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="text-2xl">
                      {spResult.meets_threshold ? "⚠️" : "✅"}
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-gray-800">
                        {spResult.meets_threshold
                          ? "Substantial Presence Test erfüllt"
                          : "Substantial Presence Test NICHT erfüllt"}
                      </h2>
                    </div>
                  </div>

                  <div className="grid gap-5 sm:grid-cols-2">
                    <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                      <h3 className="font-semibold text-gray-800 text-sm mb-3">
                        Berechnung
                      </h3>
                      <dl className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Aktuelle Tage</dt>
                          <dd className="font-medium text-gray-800">
                            {spResult.current_year_days}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Vorjahr (gewichtet)</dt>
                          <dd className="font-medium text-gray-800">
                            {spResult.prior_year_days_weighted}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Vorvorjahr (gewichtet)</dt>
                          <dd className="font-medium text-gray-800">
                            {spResult.two_years_ago_days_weighted}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm border-t border-gray-200 pt-2 mt-2">
                          <dt className="font-semibold text-gray-700">Gesamt</dt>
                          <dd className="font-bold text-gray-800">
                            {spResult.total_days_counted}
                          </dd>
                        </div>
                        <div className="flex justify-between text-sm">
                          <dt className="text-gray-500">Schwelle</dt>
                          <dd className="font-medium text-gray-800">
                            {spResult.threshold}
                          </dd>
                        </div>
                      </dl>
                    </div>

                    <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                      <h3 className="font-semibold text-gray-800 text-sm mb-3">
                        Erklärung
                      </h3>
                      <p className="text-sm text-gray-600">{spResult.explanation}</p>
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
              Übersicht: Form 8843
            </h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Zweck</h3>
                <p className="text-sm text-gray-600">{overview.purpose}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Wer muss einreichen?</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  {overview.who_must_file.map((item, i) => (
                    <li key={i}>• {item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Exempt Visumtypen</h3>
                <div className="flex flex-wrap gap-2">
                  {overview.exempt_visa_types.map((vt, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700"
                    >
                      {vt}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Substantial Presence Test</h3>
                <div className="rounded-lg bg-gray-50 p-4">
                  <dl className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-500">Schwelle</dt>
                      <dd className="font-medium text-gray-800">
                        {overview.substantial_presence_test.threshold_days} Tage
                      </dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-500">Mindesttage aktuelles Jahr</dt>
                      <dd className="font-medium text-gray-800">
                        {overview.substantial_presence_test.min_current_year_days} Tage
                      </dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-500">Formel</dt>
                      <dd className="font-medium text-gray-800">
                        {overview.substantial_presence_test.formula}
                      </dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-500">Gesetzliche Grundlage</dt>
                      <dd className="font-medium text-gray-800">
                        {overview.substantial_presence_test.statutory_reference}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Wichtige Anforderungen</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  {overview.key_requirements.map((req, i) => (
                    <li key={i}>• {req}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Frist</h3>
                <p className="text-sm text-gray-600">{overview.filing_deadline}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">IRS Referenz</h3>
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
