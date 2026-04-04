import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FireSing",
  description: "AI-powered song modification platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-gray-50">
        <header className="bg-white border-b px-6 py-3 flex items-center gap-3">
          <a href="/" className="text-xl font-bold text-gray-900">FireSing</a>
          <span className="text-sm text-gray-500">AI 方言翻唱</span>
        </header>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
