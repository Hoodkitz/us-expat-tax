import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "US Expat Tax | Mandanten-Dashboard",
  description:
    "Steuerberechnung für US-Bürger in Deutschland – FTC / FEIE Optimierung",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        {children}
        <footer
          role="contentinfo"
          className="mx-auto max-w-5xl px-4 py-6 text-xs text-gray-500"
        >
          Nur unverbindliche Orientierungswerte. Diese Software leistet keine
          Steuer-, Rechts- oder Buchhaltungsberatung und ersetzt keinen
          Steuerberater, CPA oder Enrolled Agent. Die Verantwortung für Ihre
          Steuererklärungen liegt allein bei Ihnen. / Estimates only – not tax,
          legal or accounting advice.
        </footer>
      </body>
    </html>
  );
}
