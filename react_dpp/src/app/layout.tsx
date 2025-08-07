import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "현대제철 DPP 공정표",
  description: "현대제철 DPP 생산 공정표 관리 시스템",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
