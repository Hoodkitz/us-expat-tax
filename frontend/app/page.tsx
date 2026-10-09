import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 z-50 w-full border-b border-gray-100 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🇺🇸</span>
            <span className="text-xl font-bold text-gray-900">US Expat Tax</span>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm font-medium text-gray-600 hover:text-gray-900">
              Features
            </a>
            <a href="#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900">
              Pricing
            </a>
            <a href="#faq" className="text-sm font-medium text-gray-600 hover:text-gray-900">
              FAQ
            </a>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/auth/login"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              Anmelden
            </Link>
            <Link
              href="/auth/register"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-blue-700 transition-colors"
            >
              Kostenlos starten
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-32 pb-20 sm:pt-40 sm:pb-28">
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-indigo-50" />
          <div className="absolute top-0 right-0 -translate-y-1/4 translate-x-1/4 w-96 h-96 bg-blue-200 rounded-full blur-3xl opacity-30" />
          <div className="absolute bottom-0 left-0 translate-y-1/4 -translate-x-1/4 w-96 h-96 bg-indigo-200 rounded-full blur-3xl opacity-30" />
        </div>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500"></span>
              </span>
              Jetzt für 2025 Steuerjahr verfügbar
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-6xl lg:text-7xl">
              US-Steuern für Expats.
              <br />
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Einfach gemacht.
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-600 sm:text-xl">
              Berechnen Sie Ihre Foreign Earned Income Exclusion (FEIE), optimieren Sie Ihre
              Steuerlast zwischen FTC und FEIE, und erstellen Sie Form 2555 – alles in einem
              einfachen Dashboard.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/auth/register"
                className="w-full rounded-xl bg-blue-600 px-8 py-4 text-center text-base font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 transition-all hover:shadow-xl hover:shadow-blue-600/30 sm:w-auto"
              >
                Jetzt kostenlos registrieren
              </Link>
              <a
                href="#pricing"
                className="w-full rounded-xl border border-gray-300 bg-white px-8 py-4 text-center text-base font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition-colors sm:w-auto"
              >
                Preise ansehen
              </a>
            </div>
            <p className="mt-6 text-sm text-gray-500">
              Keine Kreditkarte erforderlich · 14 Tage kostenlos testen · Jederzeit kündbar
            </p>
          </div>

          {/* Stats */}
          <div className="mx-auto mt-20 grid max-w-4xl grid-cols-2 gap-8 sm:grid-cols-4">
            {[
              { value: "2.500+", label: "Aktive Nutzer" },
              { value: "€180K+", label: "Ersparnis erzielt" },
              { value: "99,9%", label: "Verfügbarkeit" },
              { value: "4,9/5", label: "Bewertung" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold text-gray-900 sm:text-4xl">{stat.value}</div>
                <div className="mt-1 text-sm text-gray-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-gray-50 py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Alles was Sie brauchen für Ihre US-Steuererklärung
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-600">
              Von der FEIE-Berechnung bis zum Form 2555 – wir automatisieren den gesamten Prozess.
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: "🧮",
                title: "FEIE-Berechnung",
                desc: "Automatische Berechnung der Foreign Earned Income Exclusion mit aktuellen IRS-Grenzen. Sie sehen sofort, wie viel Einkommen steuerfrei bleibt.",
              },
              {
                icon: "📋",
                title: "Form 2555 Generator",
                desc: "Erstellen Sie Ihr Form 2555 mit wenigen Klicks. Alle Felder werden automatisch ausgefüllt und das Formular kann direkt exportiert werden.",
              },
              {
                icon: "📊",
                title: "Steuerplanung",
                desc: "Vergleichen Sie FTC vs. FEIE und sehen Sie, welche Strategie für Sie günstiger ist. Inklusive Child Tax Credit Optimierung.",
              },
              {
                icon: "⏰",
                title: "Deadline-Tracking",
                desc: "Verpassen Sie nie wieder eine Frist. Automatische Erinnerungen für alle wichtigen Deadlines – vom 15. April bis zum 15. Oktober.",
              },
              {
                icon: "📁",
                title: "Dokumentenverwaltung",
                desc: "Laden Sie alle relevanten Dokumente hoch und behalten Sie den Überblick. Lohnsteuerbescheinigungen, Kontoauszüge und mehr.",
              },
              {
                icon: "🔒",
                title: "Sicher & DSGVO-konform",
                desc: "Ihre Daten werden verschlüsselt übertragen und gespeichert. Server in Deutschland – vollständig DSGVO-konform.",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mb-4 text-4xl">{feature.icon}</div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Einfaches, transparentes Pricing
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-600">
              Wählen Sie den Plan, der zu Ihnen passt. Jederzeit kündbar.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-5xl gap-8 lg:grid-cols-3">
            {/* Starter */}
            <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900">Starter</h3>
              <p className="mt-1 text-sm text-gray-500">Für einfache Steuererklärungen</p>
              <div className="mt-6">
                <span className="text-4xl font-bold text-gray-900">19€</span>
                <span className="text-gray-500">/Monat</span>
              </div>
              <ul className="mt-8 space-y-4">
                {[
                  "FEIE-Berechnung",
                  "Form 2555 Generator",
                  "1 Steuerjahr",
                  "E-Mail Support",
                  "Basis-Dokumentenverwaltung",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-gray-600">
                    <svg className="h-5 w-5 flex-shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                href="/auth/register?plan=starter"
                className="mt-8 block w-full rounded-xl border border-gray-300 bg-white px-6 py-3 text-center text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition-colors"
              >
                Starter wählen
              </Link>
            </div>

            {/* Professional - Most Popular */}
            <div className="relative rounded-2xl border-2 border-blue-600 bg-white p-8 shadow-lg">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <span className="rounded-full bg-blue-600 px-4 py-1 text-xs font-semibold text-white">
                  Beliebteste Wahl
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Professional</h3>
              <p className="mt-1 text-sm text-gray-500">Für die meisten Expats</p>
              <div className="mt-6">
                <span className="text-4xl font-bold text-gray-900">29€</span>
                <span className="text-gray-500">/Monat</span>
              </div>
              <ul className="mt-8 space-y-4">
                {[
                  "Alles aus Starter",
                  "Unbegrenzte Steuerjahre",
                  "Steuerplanung & FTC-Vergleich",
                  "Deadline-Tracking & Erinnerungen",
                  "Prioritäts-Support",
                  "Erweiterte Dokumentenverwaltung",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-gray-600">
                    <svg className="h-5 w-5 flex-shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                href="/auth/register?plan=professional"
                className="mt-8 block w-full rounded-xl bg-blue-600 px-6 py-3 text-center text-sm font-semibold text-white shadow hover:bg-blue-700 transition-colors"
              >
                Professional wählen
              </Link>
            </div>

            {/* Premium */}
            <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900">Premium</h3>
              <p className="mt-1 text-sm text-gray-500">Für komplexe Situationen</p>
              <div className="mt-6">
                <span className="text-4xl font-bold text-gray-900">49€</span>
                <span className="text-gray-500">/Monat</span>
              </div>
              <ul className="mt-8 space-y-4">
                {[
                  "Alles aus Professional",
                  "FBAR / FATCA Beratung",
                  "Persönlicher Steuerberater",
                  "Telefonischer Support",
                  "Prioritäts-Verarbeitung",
                  "API-Zugang",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-gray-600">
                    <svg className="h-5 w-5 flex-shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                href="/auth/register?plan=premium"
                className="mt-8 block w-full rounded-xl border border-gray-300 bg-white px-6 py-3 text-center text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50 transition-colors"
              >
                Premium wählen
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="bg-gray-50 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Häufige Fragen
            </h2>
          </div>

          <div className="mt-12 space-y-6">
            {[
              {
                q: "Was ist die Foreign Earned Income Exclusion (FEIE)?",
                a: "Die FEIE erlaubt US-Bürgern, die im Ausland leben und arbeiten, einen Teil ihres ausländischen Einkommens von der US-Besteuerung auszuschließen. Für 2025 beträgt die maximale Ausschlussgrenze $126.500.",
              },
              {
                q: "Wie unterscheiden sich FTC und FEIE?",
                a: "Der Foreign Tax Credit (FTC) rechnet gezahlte ausländische Steuern auf Ihre US-Steuerschuld an, während die FEIE einen Teil Ihres Einkommens komplett von der Besteuerung ausschließt. Wir berechnen beide Optionen und empfehlen die günstigere.",
              },
              {
                q: "Brauche ich ein Form 2555?",
                a: "Ja, um die FEIE in Anspruch zu nehmen, müssen Sie das Form 2555 bei Ihrer US-Steuererklärung einreichen. Unser Tool generiert das Formular automatisch mit Ihren Daten.",
              },
              {
                q: "Sind meine Daten sicher?",
                a: "Absolut. Alle Daten werden verschlüsselt übertragen (TLS 1.3) und gespeichert. Unsere Server stehen in Deutschland und wir erfüllen vollständig die DSGVO-Anforderungen.",
              },
              {
                q: "Kann ich jederzeit kündigen?",
                a: "Ja, Sie können jederzeit kündigen. Es gibt keine Mindestlaufzeit und keine Kündigungsfristen. Ihre Daten bleiben 30 Tage nach Kündigung verfügbar.",
              },
              {
                q: "Gibt es eine kostenlose Testphase?",
                a: "Ja, alle Pläne kommen mit einer 14-tägigen kostenlosen Testphase. Keine Kreditkarte erforderlich.",
              },
            ].map((faq) => (
              <div key={faq.q} className="rounded-xl border border-gray-200 bg-white p-6">
                <h3 className="text-base font-semibold text-gray-900">{faq.q}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-16 sm:px-16 sm:py-20">
            <div className="absolute inset-0 -z-0">
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
              <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
            </div>
            <div className="relative z-10 text-center">
              <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Bereit, Ihre US-Steuern zu vereinfachen?
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-blue-100">
                Starten Sie noch heute mit Ihrer kostenlosen Testphase und sparen Sie Zeit und Geld.
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link
                  href="/auth/register"
                  className="w-full rounded-xl bg-white px-8 py-4 text-center text-base font-semibold text-blue-600 shadow-lg hover:bg-blue-50 transition-colors sm:w-auto"
                >
                  Jetzt kostenlos starten
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-gray-50 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">🇺🇸</span>
                <span className="text-lg font-bold text-gray-900">US Expat Tax</span>
              </div>
              <p className="mt-4 text-sm text-gray-500">
                Software für US-Expats zur einfachen Erstellung ihrer US-Steuererklärung.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900">Produkt</h4>
              <ul className="mt-4 space-y-2">
                <li><a href="#features" className="text-sm text-gray-500 hover:text-gray-700">Features</a></li>
                <li><a href="#pricing" className="text-sm text-gray-500 hover:text-gray-700">Pricing</a></li>
                <li><a href="#faq" className="text-sm text-gray-500 hover:text-gray-700">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900">Rechtliches</h4>
              <ul className="mt-4 space-y-2">
                <li><a href="/impressum" className="text-sm text-gray-500 hover:text-gray-700">Impressum</a></li>
                <li><a href="/datenschutz" className="text-sm text-gray-500 hover:text-gray-700">Datenschutz</a></li>
                <li><a href="/agb" className="text-sm text-gray-500 hover:text-gray-700">AGB</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900">Kontakt</h4>
              <ul className="mt-4 space-y-2">
                <li><a href="mailto:support@usexpattax.de" className="text-sm text-gray-500 hover:text-gray-700">support@usexpattax.de</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 border-t border-gray-200 pt-8 text-center">
            <p className="text-sm text-gray-400">
              © {new Date().getFullYear()} US Expat Tax. Alle Rechte vorbehalten.
            </p>
            <p className="mt-2 text-xs text-gray-400">
              Diese Software ersetzt keine Steuerberatung. Konsultieren Sie bei komplexen Fragen einen Steuerberater.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
