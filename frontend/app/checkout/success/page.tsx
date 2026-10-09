"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function CheckoutSuccessPage() {
  const [status, setStatus] = useState<"loading" | "success">("loading");

  useEffect(() => {
    // Simuliere eine kurze Verzögerung für die Seitenladezeit
    const timer = setTimeout(() => setStatus("success"), 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        {status === "loading" ? (
          <>
            <div className="mx-auto mb-6 h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
            <h1 className="text-xl font-semibold text-gray-900">Wird verarbeitet…</h1>
          </>
        ) : (
          <>
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
              <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Zahlung erfolgreich!</h1>
            <p className="mt-3 text-gray-600">
              Vielen Dank für Ihre Registrierung. Ihr Konto wurde aktiviert und Sie können jetzt
              auf alle Funktionen zugreifen.
            </p>
            <Link
              href="/dashboard"
              className="mt-8 block w-full rounded-xl bg-blue-600 px-6 py-3 text-center text-sm font-semibold text-white shadow hover:bg-blue-700 transition-colors"
            >
              Zum Dashboard
            </Link>
          </>
        )}
      </div>
    </main>
  );
}
