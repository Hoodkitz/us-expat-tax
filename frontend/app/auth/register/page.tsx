"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiRegister } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwörter stimmen nicht überein.");
      return;
    }
    if (password.length < 8) {
      setError("Das Passwort muss mindestens 8 Zeichen lang sein.");
      return;
    }
    setLoading(true);
    try {
      await apiRegister(email, password, tenantName || email);
      router.push("/auth/login");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="mb-8 text-center">
          <Link href="/" className="text-2xl font-extrabold text-brand-800">
            🇺🇸 US Expat Tax
          </Link>
          <h1 className="mt-3 text-xl font-semibold text-gray-700">
            Mandant registrieren
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Erstellen Sie Ihr Mandantenkonto.
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          {error && (
            <div className="mb-5 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                E-Mail-Adresse <span className="text-red-500">*</span>
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="mandant@beispiel.de"
              />
            </div>

            <div>
              <label
                htmlFor="tenant_name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Firmen- oder Privatname{" "}
                <span className="text-gray-400 text-xs">(optional)</span>
              </label>
              <input
                id="tenant_name"
                type="text"
                autoComplete="organization"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="Mustermann GmbH"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Passwort <span className="text-red-500">*</span>
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="Mindestens 8 Zeichen"
              />
            </div>

            <div>
              <label
                htmlFor="confirm_password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Passwort bestätigen <span className="text-red-500">*</span>
              </label>
              <input
                id="confirm_password"
                type="password"
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white shadow hover:bg-brand-700 transition-colors disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
            >
              {loading ? "Wird registriert …" : "Konto erstellen"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Bereits ein Konto?{" "}
            <Link
              href="/auth/login"
              className="font-medium text-brand-600 hover:underline"
            >
              Anmelden
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
