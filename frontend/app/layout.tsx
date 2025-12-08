import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/shared/Header";
import Footer from "@/components/shared/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "NATO Opportunities | Find and Track NATO Contracting Opportunities",
    template: "%s | NATO Opportunities"
  },
  description: "Stay informed about NATO contracting opportunities. Track RFPs, RFIs, and other procurement opportunities from NATO bodies including ACT, NCIA, and DIANA.",
  keywords: [
    "NATO",
    "NATO opportunities",
    "NATO contracting",
    "RFP",
    "RFI",
    "procurement",
    "government contracting",
    "NATO ACT",
    "NATO NCIA",
    "NATO DIANA"
  ],
  authors: [{ name: "NATO Opportunities" }],
  creator: "NATO Opportunities",
  publisher: "NATO Opportunities",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen antialiased flex flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

