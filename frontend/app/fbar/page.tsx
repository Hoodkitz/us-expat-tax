"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiMe,
  apiFBARJson,
  apiFBARPdf,
  FBARReport,
  FBAReporter,
  ForeignAccount,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Default empty account
// ---------------------------------------------------------------------------
function emptyAccount(): ForeignAccount {
  return {
    institution_name: "",
    country: "",
    account_number: "",
    max_balance_usd: "",
  };
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function FBARPage() {
  const router = useRouter();

  // Auth
  const [authReady, setAuthReady] = useState(false);

  // Reporter fields
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [zip, setZip] = useState("");
  const [country, setCountry] = useState("US");
  const [ssnLast4, setSsnLast4] = useState("");
  const [year, setYear] = useState<number>(new Date().getFullYear() - 1);

  // Accounts
  const [accounts, setAccounts] = useState<ForeignAccount[]>([emptyAccount()]);

  // Results
  const [jsonResult, setJsonResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingJson, setLoadingJson] = useState(false);
  const [loadingPdf, setLoadingPdf] = useState(false);

  // ---- Auth guard ----
  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }
    apiMe()
      .then(() => setAuthReady(true))
      .catch(() => {
        localStorage.removeItem("jwt_token");
        router.replace("/auth/login");
      });
  }, [router]);

  // ---------------------------------------------------------------------------
  // Account list helpers
  // ---------------------------------------------------------------------------
  function updateAccount(
    idx: number,
    field: keyof ForeignAccount,
    value: string
  ) {
    setAccounts((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], [field]: value };
      return next;
    });
  }

  function addAccount() {
    setAccounts((prev) => [...prev, emptyAccount()]);
  }

  function removeAccount(idx: number) {
    setAccounts((prev) => prev.filter((_, i) => i !== idx));
  }

  // ---------------------------------------------------------------------------
  // Build report payload
  // ---------------------------------------------------------------------------
  function buildReport(): FBARReport {
    const reporter: FBAReporter = {
      name,
      address,
      city,
      state,
      zip,
      country,
      ssn_last4: ssnLast4,
    };
    return { reporter, year, accounts };
  }

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------
  async function handleJsonReport(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setJsonResult(null);
    setLoadingJson(true);
    try {
      const data = await apiFBARJson(buildReport());
      setJsonResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoadingJson(false);
    }
  }

  async function handlePdfDownload(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoadingPdf(true);
    try {
      const blob = await apiFBARPdf(buildReport());
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `fbar_${year}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoadingPdf(false);
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
        <span className="font-extrabold text-brand-800 text-lg">
          🇺🇸 US Expat Tax
        </span>
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Dashboard
          </Link>
          <Link
            href="/history"
            className="rounded-lg border border-brand-300 px-4 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
          >
            Verlauf
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
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            FBAR — FinCEN 114 Report Generator
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Report of Foreign Bank and Financial Accounts. File electronically
            at{" "}
            <a
              href="https://bsaefiling.fincen.treas.gov"
              target="_blank"
              rel="noreferrer"
              className="text-brand-600 underline"
            >
              bsaefiling.fincen.treas.gov
            </a>
          </p>
        </div>

        <form className="space-y-8">
          {/* ---- Tax Year ---- */}
          <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-base font-semibold text-gray-800 mb-4">
              Tax Year
            </h2>
            <input
              type="number"
              min={2000}
              max={2099}
              required
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value, 10))}
              className="w-32 rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </section>

          {/* ---- Reporter Info ---- */}
          <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-base font-semibold text-gray-800 mb-4">
              Filer Information
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="Jane Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  SSN Last 4 Digits <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  maxLength={4}
                  value={ssnLast4}
                  onChange={(e) => setSsnLast4(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="1234"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Address
                </label>
                <input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="123 Main St"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  City
                </label>
                <input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="Springfield"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    State
                  </label>
                  <input
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    placeholder="IL"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ZIP
                  </label>
                  <input
                    value={zip}
                    onChange={(e) => setZip(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    placeholder="62701"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Country
                </label>
                <input
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="US"
                />
              </div>
            </div>
          </section>

          {/* ---- Accounts ---- */}
          <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-gray-800">
                Foreign Financial Accounts
              </h2>
              <button
                type="button"
                onClick={addAccount}
                className="rounded-lg border border-brand-300 px-3 py-1.5 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
              >
                + Add Account
              </button>
            </div>

            {accounts.map((acc, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Account {idx + 1}
                  </span>
                  {accounts.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeAccount(idx)}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Remove
                    </button>
                  )}
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Institution Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      required
                      value={acc.institution_name}
                      onChange={(e) =>
                        updateAccount(idx, "institution_name", e.target.value)
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      placeholder="Deutsche Bank"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Country <span className="text-red-500">*</span>
                    </label>
                    <input
                      required
                      value={acc.country}
                      onChange={(e) =>
                        updateAccount(idx, "country", e.target.value)
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      placeholder="DE"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Account Number <span className="text-red-500">*</span>
                    </label>
                    <input
                      required
                      value={acc.account_number}
                      onChange={(e) =>
                        updateAccount(idx, "account_number", e.target.value)
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      placeholder="DE89 3704 0044 0532 0130 00"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Max Balance (USD) <span className="text-red-500">*</span>
                    </label>
                    <input
                      required
                      type="number"
                      min="0"
                      step="0.01"
                      value={acc.max_balance_usd}
                      onChange={(e) =>
                        updateAccount(idx, "max_balance_usd", e.target.value)
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      placeholder="15000"
                    />
                  </div>
                </div>
              </div>
            ))}
          </section>

          {/* ---- Error ---- */}
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* ---- Buttons ---- */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              type="submit"
              disabled={loadingJson}
              onClick={handleJsonReport}
              className="flex-1 rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
            >
              {loadingJson ? "Generating…" : "JSON Report"}
            </button>
            <button
              type="button"
              disabled={loadingPdf}
              onClick={handlePdfDownload}
              className="flex-1 rounded-lg bg-gray-800 py-3 text-sm font-semibold text-white shadow hover:bg-gray-900 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-gray-600 focus:ring-offset-2"
            >
              {loadingPdf ? "Generating PDF…" : "⬇ Download PDF"}
            </button>
          </div>
        </form>

        {/* ---- JSON Result Table ---- */}
        {jsonResult && (
          <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
            <h2 className="text-base font-semibold text-gray-800">
              FBAR Report Summary
            </h2>

            {/* Meta */}
            <div className="grid gap-2 sm:grid-cols-3 text-sm">
              <div className="rounded-lg bg-gray-50 border border-gray-200 px-4 py-3">
                <p className="text-xs text-gray-500 mb-1">Tax Year</p>
                <p className="font-semibold text-gray-800">
                  {jsonResult.fbar_data?.year}
                </p>
              </div>
              <div className="rounded-lg bg-gray-50 border border-gray-200 px-4 py-3">
                <p className="text-xs text-gray-500 mb-1">Total Accounts</p>
                <p className="font-semibold text-gray-800">
                  {jsonResult.fbar_data?.total_accounts}
                </p>
              </div>
              <div
                className={`rounded-lg border px-4 py-3 ${
                  jsonResult.fbar_data?.fbar_required
                    ? "bg-yellow-50 border-yellow-300"
                    : "bg-green-50 border-green-200"
                }`}
              >
                <p className="text-xs text-gray-500 mb-1">FBAR Required</p>
                <p
                  className={`font-semibold ${
                    jsonResult.fbar_data?.fbar_required
                      ? "text-yellow-800"
                      : "text-green-800"
                  }`}
                >
                  {jsonResult.fbar_data?.fbar_required ? "⚠ YES" : "✓ No"}
                </p>
              </div>
            </div>

            {/* Accounts table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-100 text-left text-xs uppercase tracking-wide text-gray-600">
                    <th className="px-3 py-2 border border-gray-200">
                      Institution
                    </th>
                    <th className="px-3 py-2 border border-gray-200">
                      Country
                    </th>
                    <th className="px-3 py-2 border border-gray-200">
                      Account #
                    </th>
                    <th className="px-3 py-2 border border-gray-200 text-right">
                      Max Balance (USD)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {(jsonResult.fbar_data?.accounts ?? []).map(
                    (acc: any, i: number) => (
                      <tr
                        key={i}
                        className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}
                      >
                        <td className="px-3 py-2 border border-gray-200">
                          {acc.institution_name}
                        </td>
                        <td className="px-3 py-2 border border-gray-200">
                          {acc.country}
                        </td>
                        <td className="px-3 py-2 border border-gray-200 font-mono text-xs">
                          {acc.account_number}
                        </td>
                        <td className="px-3 py-2 border border-gray-200 text-right font-medium">
                          ${parseFloat(acc.max_balance_usd).toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                          })}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>

            <p className="text-xs italic text-gray-400">
              {jsonResult.message}
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
