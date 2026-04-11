"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-surface-container-lowest text-on-surface flex flex-col items-center justify-center gap-6 px-6">
      <span className="material-symbols-outlined text-6xl text-error">error</span>
      <h1 className="text-2xl font-bold">出了点问题</h1>
      <p className="text-on-surface-variant text-sm max-w-md text-center">
        页面加载时发生了错误，请尝试刷新页面。
      </p>
      <div className="flex gap-4">
        <button
          onClick={reset}
          className="px-6 py-3 bg-primary text-on-primary-fixed rounded-xl font-bold active:scale-95 transition-transform"
        >
          重试
        </button>
        <Link
          href="/dashboard"
          className="px-6 py-3 bg-surface-container-high rounded-xl font-bold hover:bg-surface-bright transition-colors border border-white/5"
        >
          返回我的作品
        </Link>
      </div>
    </div>
  );
}
