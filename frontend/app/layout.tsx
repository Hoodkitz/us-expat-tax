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
      </body>
    </html>
  );
}
