import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Survey Sentinel | MoSPI Microdata Intelligence Layer",
  description: "Evidence-driven intelligence layer for MoSPI/NSO government survey data validation (PLFS Microdata Engine)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased selection:bg-blue-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
