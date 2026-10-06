"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiTotalizationCheck,
  TotalizationRequest,
  TotalizationResult,
} from "@/lib/api";

export default function TotalizationPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);

  // Form
  const [country, setCountry] = useState("");
  const [employmentType, setEmploymentType] = useState<"employee" | "self_employed">("employee");
  const [yearsInUs, setYearsInUs] = useState("");
  const [yearsInCountry, setYearsInCountry] = useState("");
  const [usCitizen, setUsCitizen] = useState(true);

  // Result
  const [result, setResult] = useState<TotalizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) { router.replace("/auth/login"); return; }
    apiMe().then(() => setAuthReady(true)).catch(() => {
      localStorage.removeItem("jwt_token");
      router.replace("/auth/login");
    });
  }, [router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const payload: TotalizationRequest = {
        country,
        employment_type: employmentType,
        years_in_us: parseFloat(yearsInUs),
        years_in_country: parseFloat(yearsInCountry),
        us_citizen: usCitizen,
      };
      const data = await apiTotalizationCheck(payload);
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  if (!authReady) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <span className="font-extrabold text-brand-800 text-lg">🇺🇸 US Expat Tax</span>
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">
            Dashboard
          </Link>
          <Link href="/fbar" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">
            FBAR
          </Link>
          <Link href="/fbar-penalties" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">
            FBAR Penalties
          </Link>
          <Link href="/history" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">
            History
          </Link>
          <Link href="/auth/logout" className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 transition-colors">
            Logout
          </Link>
        </div>
      </nav>

      <main className="mx-auto max-w-3xl px-4 py-10 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            🤝 Social Security Totalization Agreement Checker
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Determine if the US has a Totalization Agreement with your country of employment
            and whether you can avoid dual Social Security taxation.
          </p>
        </div>

        {/* Form */}
        <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-5 sm:grid-cols-2">
              {/* Country */}
              <div className="sm:col-span-2">
                <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">
                  Country of Employment <span className="text-red-500">*</span>
                </label>
                <input
                  id="country"
                  type="text"
                  required
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="e.g. Germany, France, UK"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-gray-400">
                  Enter the country where you work / pay social security contributions.
                </p>
              </div>

              {/* Employment Type */}
              <div>
                <label htmlFor="empType" className="block text-sm font-medium text-gray-700 mb-1">
                  Employment Type <span className="text-red-500">*</span>
                </label>
                <select
                  id="empType"
                  value={employmentType}
                  onChange={(e) => setEmploymentType(e.target.value as "employee" | "self_employed")}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="employee">Employee</option>
                  <option value="self_employed">Self-Employed</option>
                </select>
              </div>

              {/* US Citizen */}
              <div className="flex items-center gap-3 pt-6">
                <input
                  id="usCitizen"
                  type="checkbox"
                  checked={usCitizen}
                  onChange={(e) => setUsCitizen(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="usCitizen" className="text-sm font-medium text-gray-700">
                  I am a US Citizen
                </label>
              </div>

              {/* Years in US */}
              <div>
                <label htmlFor="yearsUs" className="block text-sm font-medium text-gray-700 mb-1">
                  Years Worked in the US <span className="text-red-500">*</span>
                </label>
                <input
                  id="yearsUs"
                  type="number"
                  min="0"
                  step="0.5"
                  required
                  value={yearsInUs}
                  onChange={(e) => setYearsInUs(e.target.value)}
                  placeholder="e.g. 5"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-gray-400">40 quarters = 10 years for full US SS eligibility</p>
              </div>

              {/* Years in Country */}
              <div>
                <label htmlFor="yearsCountry" className="block text-sm font-medium text-gray-700 mb-1">
                  Years in Foreign Country <span className="text-red-500">*</span>
                </label>
                <input
                  id="yearsCountry"
                  type="number"
                  min="0"
                  step="0.5"
                  required
                  value={yearsInCountry}
                  onChange={(e) => setYearsInCountry(e.target.value)}
                  placeholder="e.g. 3"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-gray-400">Temporary assignments ≤5 years may stay under US system</p>
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
              className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60"
            >
              {loading ? "Checking…" : "Check Totalization Agreement"}
            </button>
          </form>
        </section>

        {/* Results */}
        {result && (
          <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm space-y-5">
            {/* Agreement Status Badge */}
            <div className="flex items-center gap-3">
              <span className={`text-3xl`}>{result.agreement_exists ? "✅" : "⚠️"}</span>
              <div>
                <h2 className="text-lg font-semibold text-gray-800">
                  {result.agreement_exists
                    ? "Totalization Agreement Exists"
                    : "No Totalization Agreement"}
                </h2>
                <p className="text-sm text-gray-500">
                  {result.avoid_double_taxation
                    ? "Double taxation can be avoided."
                    : "Risk of dual Social Security taxation."}
                </p>
              </div>
            </div>

            {/* Key Indicators */}
            <div className="grid gap-4 sm:grid-cols-2">
              <InfoCard
                label="Applicable SS System"
                value={result.applicable_system}
                highlight={false}
              />
              <InfoCard
                label="FICA Exempt?"
                value={result.fica_exempt ? "Yes – exempt from US FICA on foreign income" : "No – US FICA applies"}
                highlight={result.fica_exempt}
              />
              <InfoCard
                label="Avoid Double Taxation?"
                value={result.avoid_double_taxation ? "Yes" : "No – consult a tax professional"}
                highlight={result.avoid_double_taxation}
              />
            </div>

            {/* Explanation */}
            <div className="rounded-xl bg-blue-50 border border-blue-200 px-5 py-4">
              <h3 className="text-sm font-semibold text-blue-800 mb-2">📋 Explanation</h3>
              <p className="text-sm text-blue-700 leading-relaxed">{result.explanation}</p>
            </div>

            {/* Countries list (collapsed) */}
            <details className="text-sm text-gray-600">
              <summary className="cursor-pointer font-medium text-brand-700 hover:text-brand-900">
                View all {result.agreement_countries.length} countries with US Totalization Agreements
              </summary>
              <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-1">
                {result.agreement_countries.map((c) => (
                  <span key={c} className="text-xs bg-gray-100 rounded px-2 py-1">{c}</span>
                ))}
              </div>
            </details>

            <p className="text-xs italic text-gray-400">
              * This is an estimate for informational purposes. Consult a qualified tax professional
              for your specific situation.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}

function InfoCard({ label, value, highlight }: { label: string; value: string; highlight: boolean }) {
  return (
    <div className={`rounded-xl border p-4 ${highlight ? "border-green-300 bg-green-50" : "border-gray-200 bg-gray-50"}`}>
      <dt className="text-xs font-medium text-gray-500 mb-1">{label}</dt>
      <dd className={`text-sm font-semibold ${highlight ? "text-green-700" : "text-gray-800"}`}>{value}</dd>
    </div>
  );
}
