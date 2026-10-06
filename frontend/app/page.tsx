import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4">
      {/* Hero */}
      <div className="w-full max-w-3xl text-center">
        {/* Flag decorations */}
        <div className="mb-6 flex justify-center gap-3 text-4xl">
          <span title="USA">🇺🇸</span>
          <span className="text-gray-400">+</span>
          <span title="Deutschland">🇩🇪</span>
        </div>

        <h1 className="mb-4 text-4xl font-extrabold tracking-tight text-brand-800 sm:text-5xl">
          US Expat Tax
        </h1>

        <p className="mb-3 text-xl font-medium text-gray-700">
          Steuerberechnung für US-Bürger in Deutschland
        </p>

        <p className="mb-10 max-w-2xl mx-auto text-gray-500 leading-relaxed">
          Unser Mandanten-Dashboard berechnet automatisch den optimalen Weg
          zwischen dem{" "}
          <strong className="text-gray-700">
            Foreign Tax Credit (FTC)
          </strong>{" "}
          und der{" "}
          <strong className="text-gray-700">
            Foreign Earned Income Exclusion (FEIE)
          </strong>
          . Minimieren Sie Ihre US-Steuerlast – transparent und deterministisch.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/auth/login"
            className="rounded-lg bg-brand-600 px-8 py-3 text-white font-semibold shadow hover:bg-brand-700 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
          >
            Anmelden
          </Link>
          <Link
            href="/auth/register"
            className="rounded-lg border border-brand-600 px-8 py-3 text-brand-700 font-semibold hover:bg-brand-50 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
          >
            Registrieren
          </Link>
        </div>
      </div>

      {/* Feature cards */}
      <div className="mt-20 grid gap-6 sm:grid-cols-3 w-full max-w-3xl">
        {[
          {
            icon: "🧮",
            title: "FTC vs. FEIE",
            desc: "Automatischer Vergleich beider Steuerpfade – wir empfehlen die günstigere Option.",
          },
          {
            icon: "👶",
            title: "Child Tax Credit",
            desc: "CTC & ACTC werden berücksichtigt, inklusive rückerstattbarem Anteil.",
          },
          {
            icon: "🔒",
            title: "Sicheres Mandantenportal",
            desc: "JWT-gesicherte API, Ihre Daten verlassen nie unsere Server.",
          },
        ].map((f) => (
          <div
            key={f.title}
            className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
          >
            <div className="mb-3 text-3xl">{f.icon}</div>
            <h3 className="mb-2 font-semibold text-gray-800">{f.title}</h3>
            <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      <footer className="mt-16 text-xs text-gray-400">
        © {new Date().getFullYear()} US Expat Tax – Kein Steuerberatungsersatz.
      </footer>
    </main>
  );
}
