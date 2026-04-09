"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { getPlans, createOrder, type PricingPlan } from "../../lib/api";
import { useToast } from "../../components/Toast";

export default function PricingPage() {
  const { user, loading } = useAuth();
  const { addToast } = useToast();
  const [plans, setPlans] = useState<{ credits: PricingPlan[]; subscriptions: PricingPlan[] } | null>(null);
  const [buying, setBuying] = useState<string | null>(null);
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [pollingOrder, setPollingOrder] = useState<string | null>(null);

  useEffect(() => {
    getPlans().then(setPlans).catch(() => {});
  }, []);

  // Poll order status
  useEffect(() => {
    if (!pollingOrder) return;
    const interval = setInterval(async () => {
      try {
        const order = await (await import("../../lib/api")).getOrder(pollingOrder!);
        if (order.status === "paid") {
          setPollingOrder(null);
          setQrUrl(null);
          // Refresh user info
          window.location.reload();
        }
      } catch {
        // keep polling
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [pollingOrder]);

  async function handleBuy(planId: string) {
    if (!user?.authenticated) {
      window.location.href = "/login";
      return;
    }
    setBuying(planId);
    try {
      const result = await createOrder(planId);
      if (result.qr_url) {
        setQrUrl(result.qr_url);
        setPollingOrder(result.order_id);
      }
    } catch {
      addToast("error", "创建订单失败，请重试");
    } finally {
      setBuying(null);
    }
  }

  return (
    <div className="bg-surface-container-lowest min-h-screen text-on-surface pb-20 md:pb-0">
      {/* Top Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-neutral-950/80 backdrop-blur-xl flex justify-between items-center px-6 md:px-8 h-16">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-2xl font-black text-primary tracking-tighter">FireSing</Link>
          <div className="hidden md:flex gap-6 items-center">
            <Link href="/" className="text-neutral-400 hover:text-neutral-200 transition-colors duration-300">首页</Link>
            <Link href="/dashboard" prefetch={false} className="text-neutral-400 hover:text-neutral-200 transition-colors duration-300">我的作品</Link>
            <Link href="/pricing" className="text-primary font-bold border-b-2 border-primary pb-1">充值</Link>
          </div>
        </div>
        <Link href="/login" className="w-8 h-8 rounded-full overflow-hidden bg-surface-container-highest border border-white/5 hover:border-white/20 transition-colors flex items-center justify-center" title="登录">
          <span className="material-symbols-outlined text-sm text-white/60">person</span>
        </Link>
      </nav>

      <div className="pt-24 px-4 md:px-8 max-w-4xl mx-auto">

        {/* Current balance */}
        {user?.authenticated && (
          <div className="bg-surface-container-low p-4 rounded-xl border border-white/5 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-on-surface-variant text-sm">当前余额</span>
                <div className="text-3xl font-bold text-ember">{user.credits ?? 0} <span className="text-base font-normal">首</span></div>
              </div>
              {user.has_unlimited && (
                <span className="bg-ember/10 text-ember px-3 py-1 rounded-full text-sm font-medium">会员不限次</span>
              )}
            </div>
          </div>
        )}

        {/* Payment QR */}
        {qrUrl && (
          <div className="bg-surface-container-low p-6 rounded-xl border border-white/5 mb-8 text-center">
            <p className="text-on-surface-variant mb-4">请使用微信扫码支付</p>
            <img src={qrUrl} alt="支付二维码" className="mx-auto w-48 h-48" />
            <p className="text-on-surface-variant text-xs mt-4 animate-pulse">等待支付中...</p>
            <button onClick={() => { setQrUrl(null); setPollingOrder(null); }} className="text-on-surface-variant text-sm mt-2 hover:text-ember">
              取消
            </button>
          </div>
        )}

        {/* Credit plans */}
        <h2 className="text-lg font-semibold text-on-surface mb-4">按次购买</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {plans?.credits.map((plan) => (
            <div key={plan.id} className="bg-surface-container-low p-6 rounded-xl border border-white/5 flex flex-col">
              <h3 className="font-semibold text-on-surface">{plan.name}</h3>
              <p className="text-on-surface-variant text-sm mt-1">{plan.desc}</p>
              <div className="mt-4 text-2xl font-bold text-ember">
                ¥{(plan.price_fen / 100).toFixed(0)}
                <span className="text-sm font-normal text-on-surface-variant">/次</span>
              </div>
              <div className="mt-auto pt-4">
                <button
                  onClick={() => handleBuy(plan.id)}
                  disabled={buying !== null}
                  className="w-full bg-ember hover:opacity-90 text-white font-medium py-2.5 rounded-lg disabled:opacity-50 transition-colors"
                >
                  {buying === plan.id ? "处理中..." : "购买"}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Subscription plans — hidden until ready */}
      </div>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-16 flex justify-around items-center px-4 bg-black z-50 border-t border-white/5">
        <Link href="/" className="flex flex-col items-center justify-center text-neutral-500 p-2 hover:bg-neutral-800 transition-colors">
          <span className="material-symbols-outlined">home</span>
          <span className="text-xs font-medium">首页</span>
        </Link>
        <Link href="/dashboard" prefetch={false} className="flex flex-col items-center justify-center text-neutral-500 p-2 hover:bg-neutral-800 transition-colors">
          <span className="material-symbols-outlined">library_music</span>
          <span className="text-xs font-medium">我的作品</span>
        </Link>
        <Link href="/pricing" className="flex flex-col items-center justify-center text-primary bg-neutral-900/50 rounded-lg p-2">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: '"FILL" 1' }}>account_balance_wallet</span>
          <span className="text-xs font-medium">充值</span>
        </Link>
      </nav>
    </div>
  );
}
