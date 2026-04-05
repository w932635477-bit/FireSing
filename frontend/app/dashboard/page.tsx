"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  listSongs,
  uploadSong,
  statusLabel,
  type Song,
} from "@/lib/api";

const COVER_IMAGES = [
  "/images/cover-waves.webp",
  "/images/cover-mic.webp",
  "/images/cover-headphones.webp",
  "/images/cover-piano.webp",
  "/images/cover-vinyl.webp",
  "/images/cover-equalizer.webp",
];

function getCover(title: string): string {
  const hash = title.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  return COVER_IMAGES[hash % COVER_IMAGES.length];
}

function statusChip(status: string) {
  if (status === "done")
    return (
      <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-success/10 text-success text-xs font-bold">
        <span className="w-1.5 h-1.5 rounded-full bg-success" />
        完成
      </span>
    );
  if (status === "error")
    return (
      <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-error/10 text-error text-xs font-bold">
        <span className="material-symbols-outlined text-[10px]" style={{ fontVariationSettings: '"FILL" 1' }}>close</span>
        失败
      </span>
    );
  if (["uploaded", "separated", "segmented"].includes(status))
    return (
      <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-on-surface-variant/10 text-on-surface-variant text-xs font-bold">
        <span className="w-1.5 h-1.5 rounded-full border border-on-surface-variant" />
        已上传
      </span>
    );
  return (
    <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-warning/10 text-warning text-xs font-bold">
      <span className="w-1.5 h-1.5 rounded-full bg-warning" />
      处理中
    </span>
  );
}

export default function DashboardPage() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const load = useCallback(async () => {
    try {
      const data = await listSongs();
      setSongs(data.songs || []);
    } catch (e) {
      // API unavailable — use demo data for UI preview
      console.warn("API unavailable, showing demo data");
      setSongs([
        { id: "demo-1", title: "稻香", status: "done", created_at: "2025-04-01T10:00:00Z" },
        { id: "demo-2", title: "珊瑚海", status: "separating", created_at: "2025-04-02T14:30:00Z" },
        { id: "demo-3", title: "晴天", status: "uploaded", created_at: "2025-04-03T09:15:00Z" },
        { id: "demo-4", title: "七里香", status: "error", error_message: "RVC 模型加载超时", created_at: "2025-04-04T16:00:00Z" },
        { id: "demo-5", title: "简单爱", status: "done", created_at: "2025-04-04T20:00:00Z" },
        { id: "demo-6", title: "夜曲", status: "converting", created_at: "2025-04-05T08:00:00Z" },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const audio = fd.get("audio") as File;
    const lrc = fd.get("lrc") as File;
    if (!audio || audio.size === 0) return;
    setUploading(true);
    try {
      await uploadSong(audio, lrc.size > 0 ? lrc : undefined);
      dialogRef.current?.close();
      await load();
    } catch (e) {
      alert(`上传失败: ${e instanceof Error ? e.message : e}`);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen">
      {/* Top Navigation Bar */}
      <header className="fixed top-0 w-full flex justify-between items-center px-6 py-4 bg-black/60 backdrop-blur-xl z-50 shadow-[0_8px_32px_rgba(255,107,53,0.15)]">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-2xl font-black text-ember tracking-tight">FireSing</Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/dashboard" className="text-ember font-bold border-b-2 border-ember py-1">主页</Link>
            <Link href="/dashboard" className="text-white/60 font-medium hover:text-white hover:bg-white/5 px-3 py-2 rounded transition-all">音乐库</Link>
            <span className="text-white/60 font-medium hover:text-white hover:bg-white/5 px-3 py-2 rounded transition-all cursor-pointer">语音模型</span>
            <Link href="/dashboard" className="text-white/60 font-medium hover:text-white hover:bg-white/5 px-3 py-2 rounded transition-all">工作站</Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => dialogRef.current?.showModal()}
            className="bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed px-5 py-2 rounded-lg font-bold flex items-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all"
          >
            <span className="material-symbols-outlined text-lg">add_circle</span>
            上传新歌曲
          </button>
          <Link href="/login" className="w-10 h-10 rounded-full bg-surface-variant overflow-hidden cursor-pointer active:scale-[0.95] transition-transform flex items-center justify-center">
            <span className="material-symbols-outlined text-white/60">person</span>
          </Link>
        </div>
      </header>

      <div className="flex min-h-screen pt-20">
        {/* Side Navigation */}
        <aside className="hidden md:flex flex-col h-[calc(100vh-80px)] w-64 fixed left-0 bg-sidebar py-8 px-4">
          <div className="mb-8 px-2">
            <h2 className="text-white text-xl font-bold">黑曜石工作室</h2>
            <p className="text-white/40 text-sm font-medium">精英创作者中心</p>
          </div>
          <nav className="flex-1 space-y-2">
            {[
              { icon: "home", label: "主页", href: "/dashboard", active: true },
              { icon: "library_music", label: "音乐库", href: "/dashboard", active: false },
              { icon: "settings_voice", label: "语音模型", href: "/dashboard", active: false },
              { icon: "mic_external_on", label: "工作室", href: "/dashboard", active: false },
            ].map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all active:scale-[0.98] ${
                  item.active
                    ? "text-ember bg-white/5"
                    : "text-white/40 hover:text-white hover:bg-white/5"
                }`}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
          <div className="mt-auto px-2">
            <div className="p-4 rounded-xl bg-gradient-to-br from-ember/20 to-transparent border border-ember/20">
              <p className="text-white font-bold mb-2">升级至专业版</p>
              <p className="text-white/60 text-xs mb-3">解锁无限次数 AI 语音渲染</p>
              <button className="w-full bg-ember text-on-primary-fixed py-2 rounded-lg text-sm font-bold active:scale-[0.95] transition-transform">
                立即开始
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 md:ml-64 p-8 bg-surface-container-lowest">
          {/* Header Section */}
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-10 gap-6">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-2">我的作品</h1>
              <p className="text-on-surface-variant font-medium">管理您的精英 AI 生成人声轨道</p>
            </div>
            <div className="relative w-full md:w-80">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
              <input
                className="w-full bg-surface-container border-none rounded-lg pl-10 pr-4 py-2.5 text-on-surface focus:ring-2 focus:ring-ember/40 transition-all font-sans"
                placeholder="搜索您的作品..."
                type="text"
              />
            </div>
          </div>

          {/* Song Cards Grid */}
          {loading ? (
            <div className="flex items-center justify-center py-32">
              <span className="material-symbols-outlined text-5xl text-ember animate-pulse">hourglass_empty</span>
            </div>
          ) : songs.length === 0 ? (
            /* Empty State */
            <div className="flex flex-col items-center justify-center py-32 text-center">
              <div className="w-24 h-24 bg-surface-container-high rounded-full flex items-center justify-center mb-6">
                <span className="material-symbols-outlined text-5xl text-ember">library_music</span>
              </div>
              <h2 className="text-2xl font-bold mb-2">还没有作品</h2>
              <p className="text-on-surface-variant mb-8 max-w-xs">点击右上角上传第一首歌，开始您的创作之旅</p>
              <button
                onClick={() => dialogRef.current?.showModal()}
                className="bg-surface-container-high border border-white/10 px-6 py-3 rounded-lg font-bold hover:bg-surface-variant active:scale-[0.98] transition-all"
              >
                上传新歌
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {songs.map((song) => (
                <Link
                  key={song.id}
                  href={`/songs/${song.id}`}
                  className="group relative bg-surface-container-low p-6 rounded-xl transition-all duration-300 hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(255,107,53,0.1)] hover:bg-surface-container"
                >
                  <div className="aspect-square rounded-lg mb-4 overflow-hidden relative">
                    <Image
                      src={getCover(song.title)}
                      alt={song.title}
                      fill
                      className="object-cover"
                      sizes="(max-width:100%) 100vw, (max-width:50%) 50vw"
                    />
                    {/* Dark gradient overlay for text readability */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                    {song.status !== "uploaded" && song.status !== "done" && song.status !== "error" && (
                      <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center">
                        <div className="w-12 h-1 rounded-full bg-white/20 mb-2 overflow-hidden">
                          <div className="h-full bg-warning w-2/3" />
                        </div>
                        <span className="text-[10px] font-mono text-white/80">处理中</span>
                      </div>
                    )}
                    {song.status === "error" && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                        <span className="material-symbols-outlined text-error text-4xl">error</span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="material-symbols-outlined text-4xl text-white">play_circle</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className={`text-xl font-bold ${song.status === "error" ? "text-on-surface/50" : "text-on-surface"}`}>
                      {song.title}
                    </h3>
                  </div>
                  <div className="flex items-center gap-2 mb-4">
                    {statusChip(song.status)}
                    {song.created_at && (
                      <span className="text-xs font-mono text-on-surface-variant">
                        {new Date(song.created_at).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" })}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-on-surface-variant text-sm">
                        {song.status === "done" ? "equalizer" : song.status === "error" ? "warning" : "cloud_upload"}
                      </span>
                      <span className="text-xs font-mono text-on-surface-variant">
                        {song.status === "error" ? song.error_message || "处理失败" : song.status === "done" ? "完成" : "待处理"}
                      </span>
                    </div>
                    <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-white">more_vert</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <footer className="md:hidden fixed bottom-0 w-full bg-sidebar/80 backdrop-blur-lg border-t border-white/5 flex justify-around items-center py-4 px-6 z-50">
        <Link href="/dashboard" className="flex flex-col items-center gap-1 text-ember">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: '"FILL" 1' }}>home</span>
          <span className="text-[10px] font-bold">主页</span>
        </Link>
        <Link href="/dashboard" className="flex flex-col items-center gap-1 text-white/40">
          <span className="material-symbols-outlined">library_music</span>
          <span className="text-[10px] font-medium">音乐库</span>
        </Link>
        <span className="flex flex-col items-center gap-1 text-white/40 cursor-pointer">
          <span className="material-symbols-outlined">settings_voice</span>
          <span className="text-[10px] font-medium">语音模型</span>
        </span>
        <Link href="/dashboard" className="flex flex-col items-center gap-1 text-white/40">
          <span className="material-symbols-outlined">mic_external_on</span>
          <span className="text-[10px] font-medium">工作站</span>
        </Link>
      </footer>

      {/* Upload Dialog */}
      <dialog ref={dialogRef} className="rounded-2xl p-0 backdrop:bg-black/60 bg-surface-container-low border border-white/10 text-on-surface">
        <div className="p-6 w-[420px]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">上传新歌</h2>
            <button
              onClick={() => dialogRef.current?.close()}
              className="text-on-surface-variant hover:text-white transition-colors"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-on-surface-variant uppercase tracking-widest mb-2">音频文件 *</label>
              <input
                name="audio"
                type="file"
                accept=".mp3,.wav,.flac"
                required
                className="block w-full text-sm text-on-surface-variant file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-ember/20 file:text-ember hover:file:bg-ember/30 transition-colors"
              />
              <p className="text-xs text-on-surface-variant/60 mt-1">支持 MP3/WAV/FLAC，最大 50MB</p>
            </div>
            <div>
              <label className="block text-xs font-medium text-on-surface-variant uppercase tracking-widest mb-2">LRC 歌词文件（可选）</label>
              <input
                name="lrc"
                type="file"
                accept=".lrc,.txt"
                className="block w-full text-sm text-on-surface-variant file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-surface-container-high file:text-on-surface hover:file:bg-surface-variant transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={uploading}
              className="w-full py-3 bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed rounded-lg font-bold hover:brightness-110 disabled:opacity-50 active:scale-[0.98] transition-all"
            >
              {uploading ? "上传中..." : "上传"}
            </button>
          </form>
        </div>
      </dialog>
    </div>
  );
}
