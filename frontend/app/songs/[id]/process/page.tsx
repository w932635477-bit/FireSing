"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { connectProgress, type PipelineProgress } from "@/lib/api";

const STEPS = [
  { key: "separating", label: "人声分离", sub: "Vocal Split" },
  { key: "segmenting", label: "歌词切分", sub: "Lyric Split" },
  { key: "assigning", label: "音色分配", sub: "Voice Assign" },
  { key: "converting", label: "RVC 转换", sub: "RVC 模型转换" },
  { key: "chorus", label: "合唱检测", sub: "合唱识别" },
  { key: "monologue", label: "独白生成", sub: "个性化旁白" },
  { key: "mixing", label: "音频混音", sub: "多轨合成" },
  { key: "video", label: "视频生成", sub: "视频合成" },
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
    <div className="bg-surface-container-lowest text-on-surface font-sans antialiased min-h-screen">
      {/* Top Navigation */}
      <header className="fixed top-0 w-full flex justify-between items-center px-6 py-4 bg-black/60 backdrop-blur-xl z-50 shadow-[0_8px_32px_rgba(255,107,53,0.15)]">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-2xl font-black text-ember tracking-tight">FireSing</Link>
          <div className="h-6 w-px bg-white/10 mx-2" />
          <span className="text-white/60 font-medium text-sm">
            {isDone ? "处理完成" : isError ? "处理失败" : "处理中..."}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link href={`/songs/${songId}`} className="text-sm text-on-surface-variant hover:text-white transition-colors">
            ← 返回详情
          </Link>
        </div>
      </header>

      <main className="pt-32 pb-20 px-6 max-w-2xl mx-auto">
        {/* Hero Header */}
        <section className="mb-12 text-center">
          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
            {isDone ? "处理完成" : isError ? "处理失败" : (
              <>处理中 <span className="text-on-surface-variant/40 mx-2">·</span> 歌曲</>
            )}
          </h1>
          <p className="text-on-surface-variant font-mono text-sm tracking-widest uppercase">
            Obsidian 处理管线 {isDone ? "已完成" : isError ? "异常终止" : "运行中"}
          </p>
        </section>

        {/* Main Progress Visualizer */}
        <div className="relative group mb-12">
          <div className="absolute -inset-4 bg-ember/5 blur-3xl rounded-full opacity-50" />
          <div className="relative flex flex-col items-center">
            <div className={`text-[120px] font-black leading-none tracking-tighter mb-8 drop-shadow-[0_0_30px_rgba(255,107,53,0.3)] ${
              isDone ? "text-success" : isError ? "text-error" : "text-ember"
            }`}>
              {progress.pct}
              <span className="text-4xl align-top mt-8 ml-1">%</span>
            </div>

            {/* Gradient Progress Bar */}
            <div className="w-full h-4 bg-surface-container-high rounded-full overflow-hidden mb-4 p-0.5">
              <div
                className={`h-full rounded-full relative overflow-hidden transition-all duration-500 ${
                  isError
                    ? "bg-gradient-to-r from-error to-error-dim"
                    : isDone
                    ? "bg-gradient-to-r from-success to-success"
                    : "bg-gradient-to-r from-ember to-warning"
                }`}
                style={{ width: `${progress.pct}%` }}
              >
                {!isDone && !isError && <div className="absolute inset-0 progress-striped opacity-30" />}
              </div>
            </div>
            <div className="font-mono text-on-surface-variant flex items-center gap-2">
              {isDone ? (
                <>
                  <span className="material-symbols-outlined text-sm text-success" style={{ fontVariationSettings: '"FILL" 1' }}>check_circle</span>
                  全部步骤已完成
                </>
              ) : isError ? (
                <>
                  <span className="material-symbols-outlined text-sm text-error">error</span>
                  {progress.error_detail || "处理过程中出现错误"}
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-xs animate-pulse">timer</span>
                  {progress.message}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Task Status List */}
        <section className="bg-surface-container-low rounded-2xl p-2 space-y-1 shadow-2xl border border-white/5">
          {STEPS.map((step, idx) => {
            const isActive = step.key === progress.step;
            const isCompleted = currentIdx > idx || isDone;
            const isFailed = isError && step.key === progress.step_failed;

            return (
              <div
                key={step.key}
                className={`flex items-center justify-between p-4 rounded-xl transition-all ${
                  isFailed
                    ? "bg-error/5 border border-error/20"
                    : isActive
                    ? "bg-white/5 shadow-inner border border-white/5"
                    : isCompleted
                    ? "hover:bg-white/5"
                    : "opacity-40"
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    isFailed
                      ? "bg-error/20 text-error"
                      : isCompleted
                      ? "bg-success/10 text-success"
                      : isActive
                      ? "bg-warning/20 text-warning"
                      : "bg-surface-container text-on-surface-variant/40"
                  }`}>
                    <span className={`material-symbols-outlined text-xl ${
                      isFailed ? "" : isCompleted ? "" : isActive ? "animate-spin" : ""
                    }`}>
                      {isFailed ? "error" : isCompleted ? "check_circle" : isActive ? "progress_activity" : "circle"}
                    </span>
                  </div>
                  <div>
                    <p className={`font-bold ${isFailed ? "text-error" : isActive ? "text-warning" : ""}`}>
                      {step.label}
                    </p>
                    <p className="text-xs text-on-surface-variant uppercase tracking-tighter">{step.sub}</p>
                  </div>
                </div>
                <div className="font-mono text-sm">
                  {isFailed ? (
                    <span className="text-error">失败</span>
                  ) : isCompleted ? (
                    <span className="text-success bg-success/10 px-2 py-0.5 rounded">完成</span>
                  ) : isActive ? (
                    <span className="text-warning flex items-center gap-2">
                      {progress.message}
                      <span className="w-2 h-2 rounded-full bg-warning animate-pulse" />
                    </span>
                  ) : (
                    <span className="text-on-surface-variant/40">等待中</span>
                  )}
                </div>
              </div>
            );
          })}
        </section>

        {/* Action Buttons */}
        <footer className="mt-12 flex flex-col items-center gap-6">
          <div className="flex gap-4 w-full">
            <Link
              href={`/songs/${songId}`}
              className="flex-1 bg-surface-container-high hover:bg-surface-variant text-on-surface font-bold py-4 rounded-lg active:scale-[0.98] transition-all border border-white/5 text-center"
            >
              {isDone ? "查看结果" : isError ? "返回重试" : "取消任务"}
            </Link>
            {!isDone && !isError && (
              <button className="flex-[2] bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed font-black py-4 rounded-lg active:scale-[0.98] transition-all shadow-lg shadow-ember/30">
                后台运行
              </button>
            )}
            {isDone && (
              <Link
                href="/dashboard"
                className="flex-[2] bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed font-black py-4 rounded-lg active:scale-[0.98] transition-all shadow-lg shadow-ember/30 text-center"
              >
                返回工作台
              </Link>
            )}
          </div>

          {/* Technical Specs */}
          <div className="grid grid-cols-2 gap-4 w-full">
            <div className="bg-surface-container-low p-4 rounded-xl">
              <p className="text-[10px] text-on-surface-variant uppercase font-mono mb-1">处理引擎</p>
              <p className="font-mono text-sm">Obsidian-v4.2</p>
            </div>
            <div className="bg-surface-container-low p-4 rounded-xl">
              <p className="text-[10px] text-on-surface-variant uppercase font-mono mb-1">管线状态</p>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isDone ? "bg-success" : isError ? "bg-error" : "bg-warning animate-pulse"}`} />
                <p className="font-mono text-sm">
                  {isDone ? "已完成" : isError ? "错误" : `${progress.pct}%`}
                </p>
              </div>
            </div>
          </div>
        </footer>

        {/* Countdown */}
        {isDone && countdown !== null && countdown > 0 && (
          <p className="text-center text-sm text-on-surface-variant mt-4 font-mono">
            {countdown} 秒后自动跳转...
          </p>
        )}
      </main>

      {/* Bottom Navigation for Mobile */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full bg-sidebar/80 backdrop-blur-xl border-t border-white/5 flex justify-around py-4 z-50 px-6">
        <Link href="/" className="flex flex-col items-center text-white/40 active:scale-[0.95] transition-transform">
          <span className="material-symbols-outlined">home</span>
          <span className="text-[10px] mt-1 font-medium">首页</span>
        </Link>
        <Link href="/dashboard" className="flex flex-col items-center text-white/40 active:scale-[0.95] transition-transform">
          <span className="material-symbols-outlined">library_music</span>
          <span className="text-[10px] mt-1 font-medium">曲库</span>
        </Link>
        <div className="flex flex-col items-center text-ember active:scale-[0.95] transition-transform">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: '"FILL" 1' }}>mic_external_on</span>
          <span className="text-[10px] mt-1 font-bold">工作台</span>
        </div>
        <span className="flex flex-col items-center text-white/40 active:scale-[0.95] transition-transform">
          <span className="material-symbols-outlined">settings_voice</span>
          <span className="text-[10px] mt-1 font-medium">音色</span>
        </span>
      </nav>
    </div>
  );
}
