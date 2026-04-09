import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "@fontsource/material-symbols-outlined/400.css";
import { ToastProvider } from "@/components/Toast";
import { AuthProvider } from "@/contexts/AuthContext";
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
  title: "FireSing - AI 方言翻唱平台",
  description: "AI 驱动的多人多音色翻唱平台，重新定义您的音乐创作可能。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable} antialiased`}
    >
      <head>
      </head>
      <body className="bg-surface-container-lowest text-on-surface min-h-screen font-sans">
        <ToastProvider><AuthProvider>{children}</AuthProvider></ToastProvider>
      </body>
    </html>
  );
}
