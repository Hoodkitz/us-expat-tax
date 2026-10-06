"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiMe, apiEvaluate, TenantOut, TaxEvaluationResult } from "@/lib/api";

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function fmtUSD(val: string | undefined): string {
  if (!val) return "–";
  const num = parseFloat(val);
  if (isNaN(num)) return val;
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(num);
}

const FILING_LABELS: Record<string, string> = {
  MFJ: "Married Filing Jointly (MFJ)",
  Single: "Single",
  MFS: "Married Filing Separately (MFS)",
  HOH: "Head of Household (HOH)",
  QSS: "Qualifying Surviving Spouse (QSS)",
};

function strategyLabel(strategy: string): string {
  if (strategy === "FEIE")
    return "(Foreign Earned Income Exclusion - bis $126,500 steuerfrei)";
  if (strategy === "FTC")
    return "(Foreign Tax Credit - auslaendische Steuern werden angerechnet)";
  return "";
}

// -----------------------------------------------------------------------
// Main Dashboard
// -----------------------------------------------------------------------

export default function DashboardPage() {
  const router = useRouter();
  const [tenant, setTenant] = useState<TenantOut | null>(null);
  const [authError, setAuthError] = useState(false);

  // Form state
  const [fei, setFei] = useState("");
  const [git, setGit] = useState("");
  const [ustl, setUstl] = useState("");
  const [children, setChildren] = useState("0");
  const [filingStatus, setFilingStatus] = useState("MFJ");

  // Result state
  const [result, setResult] = useState<TaxEvaluationResult | null>(null);
  const [evalError, setEvalError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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

  async function handleEvaluate(e: FormEvent) {
    e.preventDefault();
    setEvalError(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await apiEvaluate({
        foreign_earned_income_usd: fei,
        german_income_tax_paid_usd: git,
        us_tax_liability_before_credits_usd: ustl,
        num_qualifying_children: parseInt(children, 10),
      });
      setResult(data);
    } catch (err: unknown) {
      setEvalError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  if (authError) return null;

  const gitNum = parseFloat(git);
  const showFbarBanner = !isNaN(gitNum) && gitNum >= 10000;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar – hidden when printing */}
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
            href="/history"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Verlauf
          </Link>
          <Link
            href="/fbar"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            FBAR
          </Link>
          <Link
            href="/fbar-penalties"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            FBAR Penalties
          </Link>
          <Link
            href="/totalization"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Totalization
          </Link>
          <Link
            href="/state-tax"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            State Tax
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
        {/* Welcome */}
        {tenant && (
          <div className="no-print">
            <h1 className="text-2xl font-bold text-gray-800">
              Willkommen, {tenant.tenant_name}!
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Mandanten-ID: {tenant.tenant_id} · Registriert:{" "}
              {new Date(tenant.created_at).toLocaleDateString("de-DE")}
            </p>
          </div>
        )}

        {/* FBAR Banner */}
        {showFbarBanner && (
          <div className="no-print rounded-lg bg-yellow-50 border border-yellow-300 px-4 py-3 text-sm text-yellow-800">
            ⚠️ <strong>FBAR-Pflicht pruefen:</strong> Auslaendische Konten ueber
            $10.000 muessen auf FinCEN Form 114 gemeldet werden.
          </div>
        )}

        {/* Evaluation Form – hidden when printing */}
        <section className="no-print rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-800 mb-6">
            Steuerberechnung (FTC / FEIE)
          </h2>

          <form onSubmit={handleEvaluate} className="space-y-6">
            <div className="grid gap-5 sm:grid-cols-2">
              {/* Foreign Earned Income */}
              <div>
                <label
                  htmlFor="fei"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Auslandseinkommen (USD){" "}
                  <span className="text-red-500">*</span>
                </label>
                <input
                  id="fei"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  value={fei}
                  onChange={(e) => setFei(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="z. B. 90000"
                />
                <p className="mt-1 text-xs text-gray-400">
                  Foreign Earned Income (FEI)
                </p>
              </div>

              {/* German Tax Paid */}
              <div>
                <label
                  htmlFor="git"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Gezahlte dt. Einkommensteuer (USD){" "}
                  <span className="text-red-500">*</span>
                </label>
                <input
                  id="git"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  value={git}
                  onChange={(e) => setGit(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="z. B. 18000"
                />
                <p className="mt-1 text-xs text-gray-400">
                  German Income Tax Paid (in USD)
                </p>
              </div>

              {/* US Tax Liability */}
              <div>
                <label
                  htmlFor="ustl"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  US-Steuerpflicht vor Credits (USD){" "}
                  <span className="text-red-500">*</span>
                </label>
                <input
                  id="ustl"
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  value={ustl}
                  onChange={(e) => setUstl(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="z. B. 15000"
                />
                <p className="mt-1 text-xs text-gray-400">
                  US Tax Liability Before Credits
                </p>
              </div>

              {/* Children */}
              <div>
                <label
                  htmlFor="children"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Anspruchsberechtigte Kinder
                </label>
                <input
                  id="children"
                  type="number"
                  min="0"
                  max="10"
                  required
                  value={children}
                  onChange={(e) => setChildren(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-gray-400">
                  Qualifying Children (CTC/ACTC)
                </p>
              </div>

              {/* Filing Status */}
              <div className="sm:col-span-2">
                <label
                  htmlFor="filing_status"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Steuerstatus (Filing Status)
                </label>
                <select
                  id="filing_status"
                  value={filingStatus}
                  onChange={(e) => setFilingStatus(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  {Object.entries(FILING_LABELS).map(([val, label]) => (
                    <option key={val} value={val}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {evalError && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {evalError}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
            >
              {loading ? "Berechnung läuft …" : "Steuer berechnen"}
            </button>
          </form>
        </section>

        {/* Results */}
        {result && (
          <div className="print-section">
            {/* Print header – visible only when printing */}
            <div className="hidden print:block mb-4 border-b border-gray-300 pb-3">
              <p className="text-sm text-gray-600">
                Mandant: <strong>{tenant?.email ?? "–"}</strong>
              </p>
              <p className="text-sm text-gray-600">
                Datum:{" "}
                <strong>{new Date().toLocaleDateString("de-DE")}</strong>
              </p>
            </div>

            <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">
                    {result.recommended_path === "FTC" ? "🏆" : "✅"}
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-800">
                      Empfehlung:{" "}
                      <span className="text-brand-700">
                        {result.recommended_path}
                      </span>
                      {strategyLabel(result.recommended_path) && (
                        <span className="ml-2 text-sm font-normal text-gray-500">
                          {strategyLabel(result.recommended_path)}
                        </span>
                      )}
                    </h2>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {result.recommendation_reason}
                    </p>
                  </div>
                </div>

                {/* PDF Export button – no-print so it doesn't appear in the PDF itself */}
                <button
                  onClick={() => window.print()}
                  className="no-print ml-4 shrink-0 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  📄 PDF exportieren
                </button>
              </div>

              <div className="grid gap-5 sm:grid-cols-2">
                {/* FTC Result */}
                <ResultCard
                  title="Foreign Tax Credit (FTC)"
                  badge={result.recommended_path === "FTC" ? "Empfohlen" : undefined}
                  rows={[
                    { label: "Anrechenbarer Credit", value: fmtUSD(result.ftc.credit_usd) },
                    { label: "Verbleibende US-Steuer", value: fmtUSD(result.ftc.resulting_tax_usd) },
                    { label: "CTC freigeschaltet", value: result.ftc.ctc_unlocked ? "Ja ✓" : "Nein" },
                    { label: "ACTC (erstattungsfähig)", value: fmtUSD(result.ftc.actc_refundable_usd) },
                  ]}
                />

                {/* FEIE Result */}
                <ResultCard
                  title="FEIE (Ausschluss)"
                  badge={result.recommended_path === "FEIE" ? "Empfohlen" : undefined}
                  rows={[
                    { label: "Ausgeschlossener Betrag", value: fmtUSD(result.feie.exclusion_usd) },
                    { label: "Verbleibende US-Steuer", value: fmtUSD(result.feie.resulting_tax_usd) },
                    { label: "CTC freigeschaltet", value: result.feie.ctc_unlocked ? "Ja ✓" : "Nein" },
                    { label: "ACTC (erstattungsfähig)", value: fmtUSD(result.feie.actc_refundable_usd) },
                  ]}
                />
              </div>

              {/* Disclaimer */}
              <p className="text-xs italic text-gray-500">
                Hinweis: Diese Berechnung ist eine Schaetzung. Bitte konsultiere
                einen qualifizierten Steuerberater.
              </p>

              <p className="text-xs text-gray-400">
                * Diese Berechnung ist eine automatisierte Orientierungshilfe
                und ersetzt keine Steuerberatung.
              </p>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

// -----------------------------------------------------------------------
// Sub-component
// -----------------------------------------------------------------------

function ResultCard({
  title,
  badge,
  rows,
}: {
  title: string;
  badge?: string;
  rows: { label: string; value: string }[];
}) {
  return (
    <div
      className={`rounded-xl border p-5 ${
        badge
          ? "border-brand-300 bg-brand-50"
          : "border-gray-200 bg-gray-50"
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-800 text-sm">{title}</h3>
        {badge && (
          <span className="rounded-full bg-brand-600 px-2.5 py-0.5 text-xs font-semibold text-white">
            {badge}
          </span>
        )}
      </div>
      <dl className="space-y-2">
        {rows.map((r) => (
          <div key={r.label} className="flex justify-between text-sm">
            <dt className="text-gray-500">{r.label}</dt>
            <dd className="font-medium text-gray-800">{r.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
