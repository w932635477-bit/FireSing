"use client";

import { useState } from "react";
import Link from "next/link";

export default function LandingNav() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      <header className="fixed top-0 w-full flex justify-between items-center px-6 py-4 bg-black/60 backdrop-blur-xl z-50 shadow-[0_8px_32px_rgba(255,107,53,0.15)]">
        <div className="text-2xl font-black text-ember tracking-tight">FireSing</div>
        <nav className="hidden md:flex gap-8 items-center">
          <Link href="/" className="text-ember font-bold border-b-2 border-ember px-3 py-2">首页</Link>
          <Link href="/dashboard" prefetch={false} className="text-white/60 font-medium hover:bg-white/10 px-3 py-2 rounded transition-colors">我的作品</Link>
          <Link href="/pricing" className="text-white/60 font-medium hover:bg-white/10 px-3 py-2 rounded transition-colors">充值</Link>
        </nav>
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            prefetch={false}
            className="bg-ember text-on-primary-fixed font-bold px-5 py-2 rounded shadow-[0_8px_32px_rgba(255,107,53,0.15)] active:scale-[0.98] transition-transform"
          >
            开始创作
          </Link>
          <Link href="/login" className="hidden md:flex w-10 h-10 rounded-full bg-surface-container-high overflow-hidden border border-white/10 items-center justify-center hover:bg-surface-variant hover:border-white/20 transition-all active:scale-[0.95]">
            <span className="material-symbols-outlined text-white/60">person</span>
          </Link>
          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden w-10 h-10 flex items-center justify-center text-white/80 hover:text-white transition-colors"
            aria-label="菜单"
          >
            <span className="material-symbols-outlined">{menuOpen ? "close" : "menu"}</span>
          </button>
        </div>
      </header>

      {/* Mobile drawer */}
      {menuOpen && (
        <div className="fixed inset-0 z-40 md:hidden" onClick={() => setMenuOpen(false)}>
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <nav
            className="absolute top-16 right-0 w-64 bg-surface-container-high border-l border-white/5 p-6 space-y-1 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <Link
              href="/"
              onClick={() => setMenuOpen(false)}
              className="block px-4 py-3 rounded-lg text-ember font-bold bg-ember/10"
            >
              首页
            </Link>
            <Link
              href="/dashboard"
              prefetch={false}
              onClick={() => setMenuOpen(false)}
              className="block px-4 py-3 rounded-lg text-white/70 font-medium hover:bg-white/5 transition-colors"
            >
              我的作品
            </Link>
            <Link
              href="/pricing"
              onClick={() => setMenuOpen(false)}
              className="block px-4 py-3 rounded-lg text-white/70 font-medium hover:bg-white/5 transition-colors"
            >
              充值
            </Link>
            <div className="border-t border-white/5 my-3" />
            <Link
              href="/login"
              onClick={() => setMenuOpen(false)}
              className="block px-4 py-3 rounded-lg text-white/70 font-medium hover:bg-white/5 transition-colors"
            >
              登录
            </Link>
          </nav>
        </div>
      )}
    </>
  );
}
