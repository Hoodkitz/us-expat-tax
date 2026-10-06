"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiMe, apiFEIECalculate, apiFEIECheckEligibility } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type FilingStatus = "single" | "married_filing_jointly" | "married_filing_separately";

interface FEIEFormState {
  tax_year: number;
  filing_status: FilingStatus;
  foreign_earned_income: string;
  housing_costs: string;
  employer_provided_housing: string;
  days_in_foreign_country: string;
  bona_fide_resident: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function usd(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function FEIEPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [step, setStep] = useState<1 | 2 | 3>(1);

  const [form, setForm] = useState<FEIEFormState>({
    tax_year: new Date().getFullYear() - 1,
    filing_status: "single",
    foreign_earned_income: "",
    housing_costs: "0",
    employer_provided_housing: "0",
    days_in_foreign_country: "",
    bona_fide_resident: false,
  });

  const [result, setResult] = useState<any>(null);
  const [eligibility, setEligibility] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Auth guard
  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) { router.replace("/auth/login"); return; }
    apiMe()
      .then(() => setAuthReady(true))
      .catch(() => { localStorage.removeItem("jwt_token"); router.replace("/auth/login"); });
  }, [router]);

  function set<K extends keyof FEIEFormState>(key: K, value: FEIEFormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  // Step 2: eligibility pre-check
  async function handleEligibilityCheck(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await apiFEIECheckEligibility({
        days_outside_us: parseInt(form.days_in_foreign_country, 10) || 0,
        bona_fide_resident: form.bona_fide_resident,
        us_citizen_or_green_card: true,
      });
      setEligibility(data);
      setStep(3);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  // Step 3: full FEIE calculation
  async function handleCalculate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await apiFEIECalculate({
        tax_year: form.tax_year,
        foreign_earned_income: parseFloat(form.foreign_earned_income) || 0,
        housing_costs: parseFloat(form.housing_costs) || 0,
        days_in_foreign_country: parseInt(form.days_in_foreign_country, 10) || 0,
        bona_fide_resident: form.bona_fide_resident,
        filing_status: form.filing_status,
        employer_provided_housing: parseFloat(form.employer_provided_housing) || 0,
      });
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  if (!authReady) return null;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <span className="font-extrabold text-brand-800 text-lg">🇺🇸 US Expat Tax</span>
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">Dashboard</Link>
          <Link href="/fbar" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">FBAR</Link>
          <Link href="/history" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">History</Link>
          <Link href="/auth/logout" className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 transition-colors">Sign Out</Link>
        </div>
      </nav>

      <main className="mx-auto max-w-3xl px-4 py-10 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Form 2555 – FEIE Assistant</h1>
          <p className="text-sm text-gray-500 mt-1">
            Foreign Earned Income Exclusion calculator. Determine if you qualify and estimate your
            exclusion amount under{" "}
            <a href="https://www.irs.gov/forms-pubs/about-form-2555" target="_blank" rel="noreferrer" className="text-brand-600 underline">
              IRC §911
            </a>.
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 text-xs font-medium">
          {(["1. Tax Info", "2. Eligibility", "3. Results"] as const).map((label, i) => (
            <span key={label} className={`px-3 py-1 rounded-full ${step === i + 1 ? "bg-brand-600 text-white" : "bg-gray-200 text-gray-500"}`}>{label}</span>
          ))}
        </div>

        {/* ---- Step 1: Tax Info & Income ---- */}
        {step === 1 && (
          <form
            onSubmit={(e) => { e.preventDefault(); setStep(2); }}
            className="space-y-6"
          >
            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
              <h2 className="text-base font-semibold text-gray-800">Tax Year & Filing Status</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tax Year <span className="text-red-500">*</span></label>
                  <input
                    type="number" min={2000} max={2099} required
                    value={form.tax_year}
                    onChange={(e) => set("tax_year", parseInt(e.target.value, 10))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Filing Status <span className="text-red-500">*</span></label>
                  <select
                    value={form.filing_status}
                    onChange={(e) => set("filing_status", e.target.value as FilingStatus)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="single">Single</option>
                    <option value="married_filing_jointly">Married Filing Jointly</option>
                    <option value="married_filing_separately">Married Filing Separately</option>
                  </select>
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
              <h2 className="text-base font-semibold text-gray-800">Income & Housing</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Foreign Earned Income (USD) <span className="text-red-500">*</span></label>
                  <input
                    type="number" min="0" step="0.01" required
                    value={form.foreign_earned_income}
                    onChange={(e) => set("foreign_earned_income", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    placeholder="100000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Housing Costs (USD)</label>
                  <input
                    type="number" min="0" step="0.01"
                    value={form.housing_costs}
                    onChange={(e) => set("housing_costs", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Employer-Provided Housing (USD)</label>
                  <input
                    type="number" min="0" step="0.01"
                    value={form.employer_provided_housing}
                    onChange={(e) => set("employer_provided_housing", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    placeholder="0"
                  />
                </div>
              </div>
            </section>

            <button type="submit" className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2">
              Next: Check Eligibility →
            </button>
          </form>
        )}

        {/* ---- Step 2: Eligibility ---- */}
        {step === 2 && (
          <form onSubmit={handleEligibilityCheck} className="space-y-6">
            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
              <h2 className="text-base font-semibold text-gray-800">Foreign Presence</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Days in Foreign Country <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number" min="0" max="366" required
                    value={form.days_in_foreign_country}
                    onChange={(e) => set("days_in_foreign_country", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    placeholder="335"
                  />
                  <p className="text-xs text-gray-400 mt-1">≥330 days satisfies the Physical Presence Test</p>
                </div>
                <div className="flex flex-col justify-center">
                  <label className="flex items-center gap-3 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={form.bona_fide_resident}
                      onChange={(e) => set("bona_fide_resident", e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="text-sm font-medium text-gray-700">Bona Fide Resident</span>
                  </label>
                  <p className="text-xs text-gray-400 mt-1 ml-7">
                    You established bona fide residence in a foreign country for an uninterrupted period
                    covering an entire tax year.
                  </p>
                </div>
              </div>
            </section>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">{error}</div>
            )}

            <div className="flex gap-3">
              <button type="button" onClick={() => setStep(1)} className="flex-1 rounded-lg border border-gray-300 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">← Back</button>
              <button type="submit" disabled={loading} className="flex-1 rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2">
                {loading ? "Checking…" : "Check Eligibility →"}
              </button>
            </div>
          </form>
        )}

        {/* ---- Step 3: Full Calculation & Results ---- */}
        {step === 3 && (
          <div className="space-y-6">
            {/* Eligibility banner */}
            {eligibility && (
              <div className={`rounded-2xl border p-5 ${eligibility.eligible ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{eligibility.eligible ? "✅" : "❌"}</span>
                  <p className={`font-semibold text-sm ${eligibility.eligible ? "text-green-800" : "text-red-800"}`}>
                    {eligibility.eligible ? "You appear to qualify for FEIE" : "You do not qualify for FEIE"}
                  </p>
                </div>
                <p className="text-xs text-gray-600">{eligibility.reason}</p>
              </div>
            )}

            {eligibility?.eligible && (
              <form onSubmit={handleCalculate}>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
                >
                  {loading ? "Calculating…" : "Calculate FEIE Exclusion"}
                </button>
              </form>
            )}

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">{error}</div>
            )}

            {/* Results */}
            {result && (
              <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-5">
                <h2 className="text-base font-semibold text-gray-800">Form 2555 Calculation Results</h2>

                {/* Key numbers grid */}
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    { label: "FEIE Annual Limit", value: usd(result.feie_limit), highlight: false },
                    { label: "FEIE Exclusion", value: usd(result.feie_exclusion), highlight: true },
                    { label: "Housing Base Amount", value: usd(result.housing_base_amount), highlight: false },
                    { label: "Housing Exclusion", value: usd(result.housing_exclusion), highlight: false },
                    { label: "Total Exclusion", value: usd(result.total_exclusion), highlight: true },
                    { label: "Taxable Income Estimate", value: usd(result.taxable_income_estimate), highlight: false },
                  ].map(({ label, value, highlight }) => (
                    <div key={label} className={`rounded-xl border px-4 py-3 ${highlight ? "bg-green-50 border-green-200" : "bg-gray-50 border-gray-200"}`}>
                      <p className="text-xs text-gray-500 mb-1">{label}</p>
                      <p className={`font-bold text-lg ${highlight ? "text-green-800" : "text-gray-800"}`}>{value}</p>
                    </div>
                  ))}
                </div>

                {/* Qualification badges */}
                <div className="flex flex-wrap gap-2">
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${result.qualifies_pp ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-500"}`}>
                    {result.qualifies_pp ? "✓" : "✗"} Physical Presence Test
                  </span>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${result.qualifies_bfr ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-500"}`}>
                    {result.qualifies_bfr ? "✓" : "✗"} Bona Fide Residence Test
                  </span>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${result.form_2555_required ? "bg-yellow-100 text-yellow-800" : "bg-gray-100 text-gray-500"}`}>
                    {result.form_2555_required ? "⚠ Form 2555 Required" : "Form 2555 Not Required"}
                  </span>
                </div>

                {/* Notes */}
                {result.notes?.length > 0 && (
                  <div className="rounded-xl bg-blue-50 border border-blue-200 p-4 space-y-1">
                    <p className="text-xs font-semibold text-blue-800 mb-2">Important Notes</p>
                    {result.notes.map((note: string, i: number) => (
                      <p key={i} className="text-xs text-blue-700">• {note}</p>
                    ))}
                  </div>
                )}

                <p className="text-xs text-gray-400 italic">
                  This is an estimate only. Consult a qualified tax professional and verify with{" "}
                  <a href="https://www.irs.gov/pub/irs-pdf/p54.pdf" target="_blank" rel="noreferrer" className="underline">IRS Publication 54</a>.
                </p>
              </section>
            )}

            <button type="button" onClick={() => { setStep(1); setResult(null); setEligibility(null); }} className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 transition-colors">
              ← Start Over
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
