import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TransformAI | Gen AI Platform for Automated Content Transformation",
  description:
    "Research-oriented platform transforming common source documents into multiple communication formats with factual accuracy, semantic preservation, and source grounding (SIH26154).",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-slate-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
