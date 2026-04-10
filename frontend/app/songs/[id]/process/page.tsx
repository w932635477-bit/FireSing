"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { connectProgress, cancelProcess, type PipelineProgress } from "@/lib/api";

const STEPS = [
  { key: "separating", label: "人声分离", sub: "Demucs 分离伴奏与人声" },
  { key: "segmenting", label: "智能分段", sub: "自动检测人声段落" },
  { key: "assigning", label: "音色分配", sub: "为每段分配 AI 音色" },
  { key: "converting", label: "RVC 转换", sub: "批量音色转换" },
  { key: "harmony", label: "和声生成", sub: "生成多声部和声" },
  { key: "chorus", label: "合唱增强", sub: "多声部合唱混音" },
  { key: "monologue", label: "独白合成", sub: "合成个性化独白" },
  { key: "mixing", label: "音频混缩", sub: "混合所有人声与伴奏" },
  { key: "video", label: "视频生成", sub: "生成竖版 MV 视频" },
];

function getStepIndex(step: string): number {
  return STEPS.findIndex((s) => s.key === step);
}

export default function ProcessPage() {
  const params = useParams();
  const router = useRouter();
  const songId = params.id as string;

  const [progress, setProgress] = useState<PipelineProgress>({
    step: "unknown",
    pct: 0,
    message: "等待开始...",
  });
  const [countdown, setCountdown] = useState<number | null>(null);

  useEffect(() => {
    const es = connectProgress(songId, (p) => {
      setProgress(p);
      if (p.step === "done" && !countdown) {
        setCountdown(3);
      }
    });
    return () => es.close();
  }, [songId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (countdown === null) return;
    if (countdown <= 0) {
      router.push(`/songs/${songId}`);
      return;
    }
    const t = setTimeout(() => setCountdown(countdown - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown, router, songId]);

  const currentIdx = getStepIndex(progress.step);
  const isDone = progress.step === "done";
  const isError = progress.step === "error";

  return (
    <div className="min-h-screen bg-surface-container-lowest text-on-surface flex flex-col items-center justify-center" style={{ backgroundImage: "radial-gradient(#1f1f22 1px, transparent 1px)", backgroundSize: "32px 32px" }}>
      {/* Top Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-neutral-950/80 backdrop-blur-xl flex justify-between items-center px-6 md:px-8 h-16 shadow-[0_20px_50px_rgba(89,23,0,0.06)]">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-2xl font-black text-primary tracking-tighter">FireSing</Link>
          <div className="hidden md:flex gap-6 items-center">
            <Link href="/" className="text-neutral-400 hover:text-neutral-200 transition-colors duration-300">首页</Link>
            <Link href="/dashboard" className="text-primary font-bold border-b-2 border-primary pb-1">我的作品</Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Link href={`/songs/${songId}`} className="text-sm text-neutral-500 hover:text-white transition-colors">
            ← 返回详情
          </Link>
        </div>
      </nav>

      {/* Main Canvas */}
      <main className="w-full max-w-7xl px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left: Status Detail */}
        <div className="lg:col-span-7 flex flex-col gap-8">
          <div className="relative">
            <h1 className="text-[5rem] md:text-[7rem] font-black text-on-surface leading-none -ml-2 tracking-tighter opacity-90 select-none">
              {progress.pct}
              <span className="text-primary">%</span>
            </h1>
            <p className="font-bold text-primary mt-4 tracking-tight flex items-center gap-3">
              {isDone ? (
                <span className="material-symbols-outlined text-success" style={{ fontVariationSettings: '"FILL" 1' }}>check_circle</span>
              ) : isError ? (
                <span className="material-symbols-outlined text-error">error</span>
              ) : (
                <span className="material-symbols-outlined animate-spin" style={{ fontVariationSettings: '"wght" 700' }}>refresh</span>
              )}
              {isDone ? "处理完成" : isError ? "处理失败" : "AI 音轨合成中"}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-4 bg-surface-container-low rounded-full overflow-hidden shadow-[0_0_20px_rgba(255,107,53,0.2)] relative">
            <div
              className={`h-full rounded-full relative overflow-hidden transition-all duration-500 ${
                isError ? "bg-error" : isDone ? "bg-success" : "bg-primary"
              }`}
              style={{ width: `${progress.pct}%` }}
            >
              {!isDone && !isError && (
                <div className="absolute inset-0" style={{
                  background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)",
                  backgroundSize: "200% 100%",
                  animation: "shimmer 1.5s infinite",
                }} />
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <p className="text-neutral-400 font-medium">
              {isDone ? "全部步骤已完成" : isError ? (progress.error_detail || "处理过程中出现错误") : <>正在进行：<span className="text-on-surface">{progress.message}</span></>}
            </p>
          </div>

          <div className="flex gap-4 mt-4">
            <button
              onClick={async () => {
                if (!isDone && !isError) {
                  try { await cancelProcess(songId); } catch {}
                }
                router.push(`/songs/${songId}`);
              }}
              className="px-8 py-3 bg-surface-container-highest text-on-surface rounded-xl font-bold hover:bg-surface-bright transition-all active:scale-95 border border-white/5"
            >
              {isDone ? "查看结果" : isError ? "返回重试" : "取消"}
            </button>
            {isDone && (
              <button
                onClick={() => router.push(`/songs/${songId}`)}
                className="px-8 py-3 bg-primary text-on-primary-fixed rounded-xl font-bold hover:opacity-90 transition-all active:scale-95 shadow-[0_0_20px_rgba(255,107,53,0.2)]"
              >
                查看结果
              </button>
            )}
          </div>

          {isDone && countdown !== null && countdown > 0 && (
            <p className="text-sm text-neutral-500 animate-pulse">{countdown} 秒后自动跳转...</p>
          )}
        </div>

        {/* Right: Step List */}
        <div className="lg:col-span-5 bg-surface-container-low/50 backdrop-blur-md p-8 rounded-3xl border border-white/5">
          <h2 className="text-sm font-bold text-outline uppercase tracking-[0.2em] mb-8">处理管线</h2>
          <div className="space-y-6 relative">
            {/* Vertical Line */}
            <div className="absolute left-[11px] top-2 bottom-2 w-0.5 opacity-20" style={{ background: "linear-gradient(to bottom, transparent, #262528, transparent)" }} />

            {STEPS.map((step, idx) => {
              const isActive = step.key === progress.step;
              const isCompleted = currentIdx > idx || isDone;
              const isFailed = isError && step.key === progress.step_failed;

              return (
                <div key={step.key} className={`flex items-start gap-6 group ${!isCompleted && !isActive && !isFailed ? "opacity-40" : ""}`}>
                  <div className={`relative z-10 flex items-center justify-center w-6 h-6 rounded-full ${isActive ? "bg-surface-container-highest border border-primary/30" : "bg-surface-container-lowest"}`}>
                    <span
                      className={`material-symbols-outlined text-xl ${
                        isFailed ? "text-error" : isCompleted ? "text-primary" : isActive ? "text-primary animate-spin" : "text-outline-variant"
                      }`}
                      style={isCompleted || isFailed ? { fontVariationSettings: '"FILL" 1' } : isActive ? { fontVariationSettings: '"wght" 700' } : {}}
                    >
                      {isFailed ? "error" : isCompleted ? "check_circle" : isActive ? "progress_activity" : "circle"}
                    </span>
                  </div>
                  <div>
                    <p className={`font-bold text-lg ${isFailed ? "text-error" : isActive ? "text-primary" : "text-on-surface"}`}>
                      {step.label}
                    </p>
                    <p className="text-sm text-outline-variant">
                      {isFailed ? "处理失败" : isCompleted ? `${step.sub} · 已完成` : isActive ? `${step.sub} · 处理中...` : `${step.sub} · 排队中`}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </main>

      {/* Background blurs */}
      <div className="fixed -bottom-32 -left-32 w-96 h-96 bg-primary/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="fixed -top-32 -right-32 w-96 h-96 bg-[#fc7d75]/10 blur-[120px] rounded-full pointer-events-none" />

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-16 flex justify-around items-center px-4 bg-black z-50 border-t border-white/5">
        <Link href="/" className="flex flex-col items-center justify-center text-neutral-500 p-2 hover:bg-neutral-800">
          <span className="material-symbols-outlined">home</span>
          <span className="text-xs font-medium">首页</span>
        </Link>
        <Link href="/dashboard" className="flex flex-col items-center justify-center text-primary bg-neutral-900/50 rounded-lg p-2">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: '"FILL" 1' }}>library_music</span>
          <span className="text-xs font-medium">我的作品</span>
        </Link>
        <Link href="/pricing" className="flex flex-col items-center justify-center text-neutral-500 p-2 hover:bg-neutral-800">
          <span className="material-symbols-outlined">account_balance_wallet</span>
          <span className="text-xs font-medium">充值</span>
        </Link>
      </nav>

      <style jsx>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
}
