"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { getPlans, createOrder, type PricingPlan } from "../../lib/api";

export default function PricingPage() {
  const { user, loading } = useAuth();
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
      alert("创建订单失败，请重试");
    } finally {
      setBuying(null);
    }
  }

  return (
    <div className="bg-surface-container-lowest min-h-screen p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-on-surface">充值</h1>
          <Link href="/dashboard" className="text-on-surface-variant hover:text-ember text-sm">
            ← 返回
          </Link>
        </div>

        {/* Current balance */}
        {user?.authenticated && (
          <div className="bg-surface-container-low p-4 rounded-xl ring-1 ring-white/5 mb-8">
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
          <div className="bg-surface-container-low p-6 rounded-xl ring-1 ring-white/5 mb-8 text-center">
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
            <div key={plan.id} className="bg-surface-container-low p-6 rounded-xl ring-1 ring-white/5 flex flex-col">
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
                  className="w-full bg-ember hover:bg-ember-dark text-white font-medium py-2.5 rounded-lg disabled:opacity-50 transition-colors"
                >
                  {buying === plan.id ? "处理中..." : "购买"}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Subscription plans — hidden until ready */}
      </div>
    </div>
  );
}
