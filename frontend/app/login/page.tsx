"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { getQrLoginUrl, pollLogin } from "../../lib/api";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading, login } = useAuth();
  const [qrState, setQrState] = useState<string | null>(null);
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle token from WeChat callback redirect
  useEffect(() => {
    const token = searchParams.get("token");
    const err = searchParams.get("error");
    if (err) {
      setError(err === "wechat_failed" ? "微信登录失败，请重试" : "登录失败");
    }
    if (token) {
      login(token);
    }
  }, [searchParams, login]);

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (!loading && user?.authenticated) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  // Start QR login
  async function startQrLogin() {
    try {
      setError(null);
      const data = await getQrLoginUrl();
      if (data.url) {
        setQrUrl(data.url);
        setQrState(data.state);
        setPolling(true);
      } else {
        setError("微信扫码登录未配置，请联系管理员");
      }
    } catch {
      setError("获取扫码链接失败");
    }
  }

  // Poll for QR scan result
  useEffect(() => {
    if (!polling || !qrState) return;
    const interval = setInterval(async () => {
      try {
        const result = await pollLogin(qrState);
        if (result.status === "ok" && result.token) {
          setPolling(false);
          login(result.token);
        }
      } catch {
        // keep polling
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [polling, qrState, login]);

  if (loading) {
    return (
      <div className="bg-surface-container-lowest min-h-screen flex items-center justify-center">
        <span className="text-on-surface-variant">加载中...</span>
      </div>
    );
  }

  return (
    <div className="bg-surface-container-lowest min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Back link */}
      <Link href="/" className="fixed top-6 left-6 z-10 flex items-center gap-1 text-on-surface-variant hover:text-ember text-sm font-medium transition-colors">
        <span className="material-symbols-outlined text-base">arrow_back</span>
        首页
      </Link>
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-ember/5 blur-[120px]" />
        <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] rounded-full bg-secondary/5 blur-[120px]" />
      </div>

      {/* Main Content */}
      <main className="relative z-10 w-full max-w-md">
        <div className="bg-surface-container-low p-8 rounded-2xl shadow-2xl border border-white/5">
          {/* Logo */}
          <div className="text-center mb-8">
            <span className="text-3xl font-black tracking-tighter text-ember">FireSing</span>
            <h1 className="text-on-surface text-lg font-medium mt-2">AI 方言翻唱平台</h1>
            <p className="text-on-surface-variant text-sm mt-1">登录后即可使用，注册送 3 首</p>
          </div>

          {error && (
            <div className="bg-error/10 border border-error/20 rounded-lg px-4 py-3 text-sm text-error text-center mb-6">
              {error}
            </div>
          )}

          {/* QR Code Login */}
          {qrUrl ? (
            <div className="text-center space-y-4">
              <p className="text-on-surface-variant text-sm">请使用微信扫描二维码登录</p>
              <div className="flex justify-center">
                <iframe
                  src={qrUrl}
                  width="300"
                  height="400"
                  frameBorder="0"
                  scrolling="no"
                  className="bg-white rounded-lg"
                />
              </div>
              {polling && (
                <p className="text-on-surface-variant text-xs animate-pulse">等待扫码中...</p>
              )}
              <button
                onClick={() => { setQrUrl(null); setPolling(false); }}
                className="text-on-surface-variant text-sm hover:text-ember transition-colors"
              >
                取消
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* WeChat QR Login */}
              <button
                onClick={startQrLogin}
                className="w-full bg-[#07C160] hover:bg-[#06ad56] text-white font-bold py-4 rounded-lg active:scale-[0.98] transition-transform shadow-lg shadow-[#07C160]/20 flex items-center justify-center gap-2"
              >
                <svg fill="currentColor" height="24" viewBox="0 0 24 24" width="24">
                  <path d="M8.5 13.5C8.22386 13.5 8 13.2761 8 13C8 12.7239 8.22386 12.5 8.5 12.5C8.77614 12.5 9 12.7239 9 13C9 13.2761 8.77614 13.5 8.5 13.5ZM12.5 13.5C12.2239 13.5 12 13.2761 12 13C12 12.7239 12.2239 12.5 12.5 12.5C12.7761 12.5 13 12.7239 13 13C13 13.2761 12.7761 13.5 12.5 13.5Z" />
                </svg>
                微信扫码登录
              </button>

              {/* Free Experience (temporary, for beta) */}
              <div className="relative flex items-center">
                <div className="flex-grow border-t border-surface-variant/50" />
                <span className="flex-shrink mx-4 text-[10px] text-on-surface-variant/40">内测阶段</span>
                <div className="flex-grow border-t border-surface-variant/50" />
              </div>

              <button
                onClick={() => router.push("/dashboard")}
                className="w-full ember-gradient text-on-primary-fixed font-bold py-3.5 rounded-lg active:scale-[0.98] transition-transform flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-xl">rocket_launch</span>
                免费体验（无需登录）
              </button>
            </div>
          )}
        </div>

        <div className="mt-6 text-center">
          <Link href="/dashboard" prefetch={false} className="text-on-surface-variant text-sm hover:text-ember transition-colors">
            直接进入工作台 →
          </Link>
        </div>
      </main>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="bg-surface-container-lowest min-h-screen flex items-center justify-center"><span className="text-on-surface-variant">加载中...</span></div>}>
      <LoginContent />
    </Suspense>
  );
}
