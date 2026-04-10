"use client";

import { useEffect, useState } from "react";

export default function GpuStatusBanner() {
  const [gpuStatus, setGpuStatus] = useState<
    "ok" | "offline" | "error" | "checking" | "unknown"
  >("unknown");

  useEffect(() => {
    let mounted = true;
    let interval: ReturnType<typeof setInterval>;

    async function check() {
      try {
        const resp = await fetch("/api/health/gpu");
        if (!mounted) return;
        if (resp.ok) {
          const data = await resp.json();
          setGpuStatus(data.status === "ok" ? "ok" : "error");
        } else {
          setGpuStatus("error");
        }
      } catch {
        if (mounted) setGpuStatus("offline");
      }
    }

    check();
    interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (gpuStatus === "ok" || gpuStatus === "unknown") return null;

  return (
    <div className="bg-amber-500/90 text-black text-sm px-4 py-2 text-center font-medium">
      GPU 服务器未连接 — 歌曲处理功能暂不可用。请启动 AutoDL 上的 GPU 服务。
    </div>
  );
}
