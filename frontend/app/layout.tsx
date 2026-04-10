import type { Metadata } from "next";
import { ToastProvider } from "@/components/Toast";
import { AuthProvider } from "@/contexts/AuthContext";
import GpuStatusBanner from "@/components/GpuStatusBanner";
import "./globals.css";

export const metadata: Metadata = {
  title: "FireSing - AI 方言翻唱平台",
  description: "上传一首歌，选几种方言音色，两分钟拿到翻唱视频。抖音、快手直接发。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="antialiased">
      <head>
        <link rel="stylesheet" href="/fonts/fonts.css" />
      </head>
      <body className="bg-surface-container-lowest text-on-surface min-h-screen font-sans">
        <GpuStatusBanner />
        <ToastProvider><AuthProvider>{children}</AuthProvider></ToastProvider>
      </body>
    </html>
  );
}
