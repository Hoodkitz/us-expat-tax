"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiFBARPenalties,
  FBARPenaltyRequest,
  FBARPenaltyResult,
} from "@/lib/api";

function fmtUSD(val: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(val);
}

export default function FBARPenaltiesPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);

  // Form
  const [violationType, setViolationType] = useState<"non_willful" | "willful" | "fraud">("non_willful");
  const [years, setYears] = useState("1");
  const [balance, setBalance] = useState("");
  const [filedLate, setFiledLate] = useState(true);
  const [voluntaryDisclosure, setVoluntaryDisclosure] = useState(false);

  // Result
  const [result, setResult] = useState<FBARPenaltyResult | null>(null);
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
      const payload: FBARPenaltyRequest = {
        violation_type: violationType,
        years_of_violation: parseInt(years, 10),
        max_account_balance: parseFloat(balance),
        filed_late: filedLate,
        voluntary_disclosure: voluntaryDisclosure,
      };
      const data = await apiFBARPenalties(payload);
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  if (!authReady) return null;

  const violationLabels = {
    non_willful: "Non-Willful (unintentional oversight)",
    willful: "Willful (intentional non-compliance)",
    fraud: "Fraud (criminal level)",
  };

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
          <Link href="/totalization" className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors">
            Totalization
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
            ⚖️ FBAR Penalties Calculator
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Estimate your FBAR penalty exposure under FinCEN / IRS guidelines (2024).
            FBAR filing is required for foreign accounts exceeding $10,000 in aggregate.
          </p>
        </div>

        {/* Info banner */}
        <div className="rounded-lg bg-yellow-50 border border-yellow-300 px-4 py-3 text-sm text-yellow-800">
          ⚠️ <strong>Important:</strong> FBAR penalties can be severe. This calculator provides
          estimates only. Always consult a qualified tax attorney for FBAR compliance issues.
        </div>

        {/* Form */}
        <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-5 sm:grid-cols-2">
              {/* Violation Type */}
              <div className="sm:col-span-2">
                <label htmlFor="violationType" className="block text-sm font-medium text-gray-700 mb-1">
                  Violation Type <span className="text-red-500">*</span>
                </label>
                <select
                  id="violationType"
                  value={violationType}
                  onChange={(e) => setViolationType(e.target.value as "non_willful" | "willful" | "fraud")}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  {Object.entries(violationLabels).map(([val, label]) => (
                    <option key={val} value={val}>{label}</option>
                  ))}
                </select>
                {violationType === "fraud" && (
                  <p className="mt-1 text-xs text-red-600 font-medium">
                    ⚠️ Fraud-level violations carry criminal prosecution risk. Retain legal counsel immediately.
                  </p>
                )}
              </div>

              {/* Years */}
              <div>
                <label htmlFor="years" className="block text-sm font-medium text-gray-700 mb-1">
                  Years of Violation <span className="text-red-500">*</span>
                </label>
                <input
                  id="years"
                  type="number"
                  min="1"
                  max="20"
                  required
                  value={years}
                  onChange={(e) => setYears(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-gray-400">Number of tax years with unreported accounts</p>
              </div>

              {/* Max Balance */}
              <div>
                <label htmlFor="balance" className="block text-sm font-medium text-gray-700 mb-1">
                  Maximum Account Balance (USD) <span className="text-red-500">*</span>
                </label>
                <input
                  id="balance"
                  type="number"
                  min="0"
                  step="100"
                  required
                  value={balance}
                  onChange={(e) => setBalance(e.target.value)}
                  placeholder="e.g. 150000"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-gray-400">Highest balance during the violation period</p>
              </div>

              {/* Checkboxes */}
              <div className="flex items-center gap-3">
                <input
                  id="filedLate"
                  type="checkbox"
                  checked={filedLate}
                  onChange={(e) => setFiledLate(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="filedLate" className="text-sm font-medium text-gray-700">
                  Filed late (or not filed)
                </label>
              </div>

              <div className="flex items-center gap-3">
                <input
                  id="voluntary"
                  type="checkbox"
                  checked={voluntaryDisclosure}
                  onChange={(e) => setVoluntaryDisclosure(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="voluntary" className="text-sm font-medium text-gray-700">
                  Voluntary Disclosure (before IRS contact)
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
              className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60"
            >
              {loading ? "Calculating…" : "Calculate FBAR Penalties"}
            </button>
          </form>
        </section>

        {/* Results */}
        {result && (
          <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm space-y-5">
            {/* Criminal risk alert */}
            {result.criminal_risk && (
              <div className="rounded-lg bg-red-50 border border-red-400 px-4 py-3 text-sm text-red-800 font-medium">
                🚨 <strong>CRIMINAL PROSECUTION RISK DETECTED.</strong> Do NOT contact the IRS without
                legal representation. Retain a tax attorney with criminal defense experience immediately.
              </div>
            )}

            {/* Penalty Range */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
                <dt className="text-xs font-medium text-gray-500 mb-1">Minimum Estimated Penalty</dt>
                <dd className="text-2xl font-bold text-gray-800">{fmtUSD(result.min_penalty)}</dd>
              </div>
              <div className="rounded-xl border border-red-200 bg-red-50 p-5">
                <dt className="text-xs font-medium text-red-600 mb-1">Maximum Estimated Penalty</dt>
                <dd className="text-2xl font-bold text-red-700">{fmtUSD(result.max_penalty)}</dd>
              </div>
            </div>

            {/* Status badges */}
            <div className="flex flex-wrap gap-3">
              <Badge
                label="Criminal Risk"
                active={result.criminal_risk}
                activeColor="red"
                inactiveLabel="No Criminal Risk"
              />
              <Badge
                label="Streamlined Eligible"
                active={result.streamlined_eligible}
                activeColor="green"
                inactiveLabel="Not Streamlined Eligible"
              />
            </div>

            {/* Penalty Breakdown */}
            <div>
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Penalty Breakdown</h3>
              <div className="space-y-2">
                {result.penalty_breakdown.map((item, i) => (
                  <div key={i} className="flex justify-between items-start rounded-lg bg-gray-50 border border-gray-100 px-4 py-3 text-sm gap-4">
                    <span className="text-gray-700 flex-1">{item.description}</span>
                    <span className={`font-semibold shrink-0 ${item.amount < 0 ? "text-green-600" : item.amount === 0 ? "text-gray-400" : "text-gray-800"}`}>
                      {item.amount === 0 ? "See above" : fmtUSD(item.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendation */}
            <div className="rounded-xl bg-blue-50 border border-blue-200 px-5 py-4">
              <h3 className="text-sm font-semibold text-blue-800 mb-2">💡 Recommendation</h3>
              <p className="text-sm text-blue-700 leading-relaxed">{result.recommendation}</p>
            </div>

            <p className="text-xs italic text-gray-400">
              * Penalty estimates are based on published IRS/FinCEN guidelines and are for
              informational purposes only. Actual penalties depend on facts and IRS discretion.
              This is not legal advice.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}

function Badge({
  label,
  active,
  activeColor,
  inactiveLabel,
}: {
  label: string;
  active: boolean;
  activeColor: "red" | "green";
  inactiveLabel: string;
}) {
  if (active) {
    const cls = activeColor === "red"
      ? "bg-red-100 text-red-700 border-red-300"
      : "bg-green-100 text-green-700 border-green-300";
    return (
      <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${cls}`}>
        {activeColor === "red" ? "⚠️" : "✅"} {label}
      </span>
    );
  }
  return (
    <span className="rounded-full border border-gray-200 bg-gray-100 px-3 py-1 text-xs text-gray-500">
      {inactiveLabel}
    </span>
  );
}
