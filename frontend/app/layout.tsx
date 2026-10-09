import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "US Expat Tax – FEIE & Form 2555 für US-Expats",
  description:
    "Berechnen Sie Ihre Foreign Earned Income Exclusion (FEIE), optimieren Sie Ihre Steuerlast zwischen FTC und FEIE, und erstellen Sie Form 2555 – alles in einem einfachen Dashboard. Ab 19€/Monat.",
  keywords: [
    "US Expat Tax",
    "FEIE",
    "Foreign Earned Income Exclusion",
    "Form 2555",
    "FTC",
    "Foreign Tax Credit",
    "US-Steuern",
    "Expat",
    "Steuerplanung",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body className={`${inter.className} min-h-screen bg-white text-gray-900 antialiased`}>
        {children}
      </body>
    </html>
  );
}
