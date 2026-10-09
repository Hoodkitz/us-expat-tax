"use client";

import Link from "next/link";

export default function CheckoutCancelPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100">
          <svg className="h-8 w-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Zahlung abgebrochen</h1>
        <p className="mt-3 text-gray-600">
          Ihre Zahlung wurde abgebrochen. Sie können es jederzeit erneut versuchen – es wurde
          nichts berechnet.
        </p>
        <div className="mt-8 space-y-3">
          <Link
            href="/#pricing"
            className="block w-full rounded-xl bg-blue-600 px-6 py-3 text-center text-sm font-semibold text-white shadow hover:bg-blue-700 transition-colors"
          >
            Erneut versuchen
          </Link>
          <Link
            href="/"
            className="block w-full rounded-xl border border-gray-300 bg-white px-6 py-3 text-center text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition-colors"
          >
            Zur Startseite
          </Link>
        </div>
      </div>
    </main>
  );
}
