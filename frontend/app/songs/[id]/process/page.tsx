"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { connectProgress, statusLabel, type PipelineProgress } from "@/lib/api";

const STEPS = [
  { key: "separating", label: "人声分离" },
  { key: "segmenting", label: "歌词切分" },
  { key: "assigning", label: "音色分配" },
  { key: "converting", label: "RVC 转换" },
  { key: "chorus", label: "合唱检测" },
  { key: "monologue", label: "独白生成" },
  { key: "mixing", label: "音频混音" },
  { key: "video", label: "视频生成" },
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
    <div className="max-w-2xl mx-auto px-6 py-12">
      <div className="mb-8">
        <Link href={`/songs/${songId}`} className="text-sm text-gray-500 hover:text-gray-700">
          ← 返回歌曲详情
        </Link>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-xl border p-6 mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-bold text-lg">
            {isDone ? "处理完成!" : isError ? "处理失败" : "处理中..."}
          </h2>
          <span className="text-2xl font-bold text-blue-600">{progress.pct}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${
              isError ? "bg-red-500" : isDone ? "bg-green-500" : "bg-blue-600"
            }`}
            style={{ width: `${progress.pct}%` }}
          />
        </div>
        <p className="text-sm text-gray-500 mt-2">{progress.message}</p>
        {isError && progress.error_detail && (
          <p className="text-sm text-red-500 mt-1">{progress.error_detail}</p>
        )}
      </div>

      {/* Step List */}
      <div className="bg-white rounded-xl border p-5">
        <div className="space-y-3">
          {STEPS.map((step, idx) => {
            const isActive = step.key === progress.step;
            const isCompleted = currentIdx > idx || isDone;
            const isFailed = isError && step.key === progress.step_failed;
            return (
              <div key={step.key} className="flex items-center gap-3">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                  isFailed ? "bg-red-100 text-red-600" :
                  isCompleted ? "bg-green-100 text-green-600" :
                  isActive ? "bg-blue-100 text-blue-600 animate-pulse" :
                  "bg-gray-100 text-gray-400"
                }`}>
                  {isFailed ? "✗" : isCompleted ? "✓" : idx + 1}
                </span>
                <span className={`flex-1 text-sm ${
                  isActive ? "font-semibold text-gray-900" :
                  isCompleted ? "text-gray-600" :
                  "text-gray-400"
                }`}>
                  {step.label}
                </span>
                {isActive && !isDone && !isError && (
                  <span className="text-xs text-blue-500 animate-pulse">进行中</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Countdown */}
      {isDone && countdown !== null && countdown > 0 && (
        <p className="text-center text-sm text-gray-500 mt-4">
          {countdown} 秒后自动跳转...
        </p>
      )}

      {/* Retry / Back */}
      {(isError || isDone) && (
        <div className="flex gap-3 mt-6 justify-center">
          {isError && (
            <Link
              href={`/songs/${songId}`}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              返回重试
            </Link>
          )}
          <Link
            href={`/songs/${songId}`}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            查看详情
          </Link>
        </div>
      )}
    </div>
  );
}
