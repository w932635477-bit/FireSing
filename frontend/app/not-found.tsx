import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-surface-container-lowest text-on-surface flex flex-col items-center justify-center gap-6 px-6">
      <span className="material-symbols-outlined text-6xl text-on-surface-variant">search_off</span>
      <h1 className="text-3xl font-black">404</h1>
      <p className="text-on-surface-variant">页面不存在或已被移除</p>
      <div className="flex gap-4">
        <Link
          href="/"
          className="px-6 py-3 bg-primary text-on-primary-fixed rounded-xl font-bold active:scale-95 transition-transform"
        >
          返回首页
        </Link>
        <Link
          href="/dashboard"
          className="px-6 py-3 bg-surface-container-high rounded-xl font-bold hover:bg-surface-bright transition-colors border border-white/5"
        >
          我的作品
        </Link>
      </div>
    </div>
  );
}
