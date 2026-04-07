"use client";

import { useState } from "react";
import Link from "next/link";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    // MVP: no real auth, direct experience
    window.location.href = "/dashboard";
  }

  return (
    <div className="bg-surface-container-lowest min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Subtle Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-ember/5 blur-[120px]" />
        <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] rounded-full bg-secondary/5 blur-[120px]" />
      </div>

      {/* Visual Accents */}
      <div className="fixed top-12 left-12 hidden lg:block">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] font-mono text-on-surface-variant/40 tracking-[0.4em] uppercase">系统状态</span>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-success shadow-[0_0_10px_rgba(48,209,88,0.5)]" />
            <span className="text-xs font-medium text-success uppercase tracking-widest">网络安全</span>
          </div>
        </div>
      </div>
      <div className="fixed bottom-12 right-12 hidden lg:block">
        <div className="flex flex-col items-end gap-1">
          <span className="text-[10px] font-mono text-on-surface-variant/40 tracking-[0.4em] uppercase">核心版本</span>
          <span className="text-xs font-mono text-on-surface-variant">v4.2.0-Obsidian</span>
        </div>
      </div>

      {/* Decorative circles */}
      <div className="fixed right-[10%] top-1/2 -translate-y-1/2 w-96 h-96 opacity-20 pointer-events-none hidden xl:block">
        <div className="relative w-full h-full">
          <div className="absolute inset-0 rounded-full border border-ember/20 animate-pulse" />
          <div className="absolute inset-10 rounded-full border border-ember/10" />
          <div className="absolute inset-20 rounded-full border border-ember/5" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-ember/40">
            <span className="material-symbols-outlined !text-9xl" style={{ fontVariationSettings: '"wght" 100' }}>graphic_eq</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="relative z-10 w-full max-w-md">
        <div className="bg-surface-container-low p-8 rounded-2xl shadow-2xl ring-1 ring-white/5">
          {/* Logo & Header */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center mb-4">
              <span className="text-3xl font-black tracking-tighter text-ember">🔥 FireSing</span>
            </div>
            <h1 className="text-on-surface text-lg font-medium tracking-tight">AI 方言翻唱平台</h1>
            <p className="text-on-surface-variant text-sm mt-1">极致性能，地道表达</p>
          </div>

          {/* Login Form */}
          <div className="bg-ember/10 border border-ember/20 rounded-lg px-4 py-3 text-sm text-ember text-center">
            内测阶段，直接体验全部功能
          </div>
          <form onSubmit={handleSubmit} className="space-y-6">
            <button
              className="w-full ember-gradient text-on-primary-fixed font-bold py-4 rounded-lg active:scale-[0.98] transition-transform shadow-lg shadow-ember/20 flex items-center justify-center gap-2"
              type="submit"
              disabled={loading}
            >
              <span className="material-symbols-outlined">rocket_launch</span>
              {loading ? "进入中..." : "免费体验"}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8 flex items-center">
            <div className="flex-grow border-t border-surface-variant/50" />
            <span className="flex-shrink mx-4 text-[10px] font-bold text-on-surface-variant/40 tracking-[0.2em]">或</span>
            <div className="flex-grow border-t border-surface-variant/50" />
          </div>

          {/* WeChat Login */}
          <button className="w-full bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-medium py-3.5 rounded-lg flex items-center justify-center gap-3 active:scale-[0.98] transition-all border border-white/5">
            <svg fill="none" height="24" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg">
              <path d="M8.5 13.5C8.22386 13.5 8 13.2761 8 13C8 12.7239 8.22386 12.5 8.5 12.5C8.77614 12.5 9 12.7239 9 13C9 13.2761 8.77614 13.5 8.5 13.5ZM12.5 13.5C12.2239 13.5 12 13.2761 12 13C12 12.7239 12.2239 12.5 12.5 12.5C12.7761 12.5 13 12.7239 13 13C13 13.2761 12.7761 13.5 12.5 13.5ZM15.5 8C15.5 4.68629 12.3657 2 8.5 2C4.63427 2 1.5 4.68629 1.5 8C1.5 10.9667 4.11603 13.4357 7.5 13.9143V16.5L10.5 14C11.5 14 14.5 13.75 15.5 12.5C14.75 12.5 13.25 12.5 12.5 12.5C11.5 12.5 10.5 11.5 10.5 10.5V10C10.5 8.89543 11.3954 8 12.5 8H15.5Z" fill="#07C160" />
              <path d="M19.5 15.5C19.2239 15.5 19 15.2761 19 15C19 14.7239 19.2239 14.5 19.5 14.5C19.7761 14.5 20 14.7239 20 15C20 15.2761 19.7761 15.5 19.5 15.5ZM16.5 15.5C16.2239 15.5 16 15.2761 16 15C16 14.7239 16.2239 14.5 16.5 14.5C16.7761 14.5 17 14.7239 17 15C17 15.2761 16.7761 15.5 16.5 15.5ZM22.5 13.5C22.5 10.7386 20.0376 8.5 17 8.5C13.9624 8.5 11.5 10.7386 11.5 13.5C11.5 16.2614 13.9624 18.5 17 18.5C17.6 18.5 18.5 18.5 19.5 19L21.5 20.5V18.5C22 18 22.5 17 22.5 15.5V13.5Z" fill="#07C160" />
            </svg>
            使用微信登录
          </button>
        </div>

        {/* Footer Link */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-on-surface-variant text-sm hover:text-ember transition-colors">
            ← 返回首页
          </Link>
        </div>
      </main>
    </div>
  );
}
