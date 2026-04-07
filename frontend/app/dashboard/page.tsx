"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  listSongs,
  uploadSong,
  deleteSong,
  searchMusic,
  importMusic,
  checkMusicExisting,
  connectImportProgress,
  statusLabel,
  type Song,
  type MusicSearchSong,
  type MusicImportProgress,
} from "@/lib/api";
import { useToast } from "@/components/Toast";

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
  const { addToast } = useToast();
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  // Music search state
  const [dialogTab, setDialogTab] = useState<"search" | "upload">("search");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<MusicSearchSong[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [importing, setImporting] = useState<string | null>(null); // song name being imported
  const [importProgress, setImportProgress] = useState<MusicImportProgress | null>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(null);

  async function handleDelete(songId: string, songTitle: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm(`确定删除「${songTitle}」？此操作不可恢复。`)) return;
    setDeleting(songId);
    try { await deleteSong(songId); await load(); }
    catch (e) { addToast("error", `删除失败: ${e instanceof Error ? e.message : "请重试"}`); }
    finally { setDeleting(null); }
  }

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
      addToast("error", `上传失败: ${e instanceof Error ? e.message : "请重试"}`);
    } finally {
      setUploading(false);
    }
  }

  function handleSearchInput(val: string) {
    setSearchQuery(val);
    setSearchError(null);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (!val.trim()) {
      setSearchResults([]);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await searchMusic(val.trim());
        setSearchResults(data.songs || []);
      } catch (e) {
        setSearchResults([]);
        const msg = e instanceof Error ? e.message : "";
        if (msg.includes("503") || msg.includes("service_unavailable") || msg.includes("unavailable")) {
          setSearchError("搜索服务暂时不可用，请稍后再试");
        } else {
          setSearchError("搜索失败，请重试");
        }
      } finally {
        setSearching(false);
      }
    }, 400);
  }

  async function handleImport(song: MusicSearchSong) {
    // Dedup check
    try {
      const { exists } = await checkMusicExisting(song.source, song.id);
      if (exists) {
        addToast("warning", "这首歌已经导入过了");
        return;
      }
    } catch {
      // If check fails, proceed anyway
    }

    setImporting(song.name);
    setImportProgress({ step: "queued", pct: 0, message: "排队中..." });
    try {
      const { task_id } = await importMusic(song.source, song.id, song.name, song.artist);
      connectImportProgress(
        task_id,
        (p) => setImportProgress(p),
        async () => {
          setImporting(null);
          setImportProgress(null);
          dialogRef.current?.close();
          await load();
        },
        (msg) => {
          addToast("error", `导入失败: ${msg}`);
          setImporting(null);
          setImportProgress(null);
        },
      );
    } catch (e) {
      addToast("error", `导入失败: ${e instanceof Error ? e.message : "请重试"}`);
      setImporting(null);
      setImportProgress(null);
    }
  }

  function handleDialogClose() {
    if (importing) {
      addToast("warning", "导入正在进行中，请等待完成");
      return;
    }
    dialogRef.current?.close();
  }

  function openDialog() {
    setSearchQuery("");
    setSearchResults([]);
    setSearchError(null);
    setImporting(null);
    setImportProgress(null);
    setDialogTab("search");
    dialogRef.current?.showModal();
  }

  return (
    <div className="min-h-screen">
      {/* Top Navigation Bar */}
      <header className="fixed top-0 w-full flex justify-between items-center px-6 py-4 bg-black/60 backdrop-blur-xl z-50 shadow-[0_8px_32px_rgba(255,107,53,0.15)]">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-2xl font-black text-ember tracking-tight">FireSing</Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/dashboard" className="text-ember font-bold border-b-2 border-ember py-1">我的作品</Link>
            <span className="text-white/20 font-medium px-3 py-2 cursor-not-allowed">音乐库 <span className="text-[9px] text-white/15">即将上线</span></span>
            <span className="text-white/20 font-medium px-3 py-2 cursor-not-allowed">语音模型 <span className="text-[9px] text-white/15">即将上线</span></span>
            <span className="text-white/20 font-medium px-3 py-2 cursor-not-allowed">工作室 <span className="text-[9px] text-white/15">即将上线</span></span>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={openDialog}
            className="bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed px-5 py-2 rounded-lg font-bold flex items-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all"
          >
            <span className="material-symbols-outlined text-lg">add_circle</span>
            添加新歌曲
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
              { icon: "home", label: "我的作品", href: "/dashboard", active: true, disabled: false },
              { icon: "library_music", label: "音乐库", disabled: true },
              { icon: "settings_voice", label: "语音模型", disabled: true },
              { icon: "mic_external_on", label: "工作室", disabled: true },
            ].map((item) => (
              item.disabled ? (
                <div key={item.label} className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/20 cursor-not-allowed">
                  <span className="material-symbols-outlined">{item.icon}</span>
                  <span>{item.label}</span>
                  <span className="text-[9px] ml-auto px-1.5 py-0.5 rounded bg-white/5 text-white/25">即将上线</span>
                </div>
              ) : (
              <Link
                key={item.label}
                href={item.href!}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all active:scale-[0.98] ${
                  item.active
                    ? "text-ember bg-white/5"
                    : "text-white/40 hover:text-white hover:bg-white/5"
                }`}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
              )
            ))}
          </nav>
          <div className="mt-auto px-2">
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
                <p className="text-white font-bold text-sm">内测阶段 · 免费</p>
              </div>
              <p className="text-white/40 text-xs">正式上线后将推出付费方案</p>
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
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
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
                onClick={openDialog}
                className="bg-surface-container-high border border-white/10 px-6 py-3 rounded-lg font-bold hover:bg-surface-variant active:scale-[0.98] transition-all"
              >
                上传新歌
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {songs
                .filter((s) => !filterQuery || s.title.toLowerCase().includes(filterQuery.toLowerCase()))
                .map((song) => (
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
                      loading="eager"
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
                    <button
                      onClick={(e) => handleDelete(song.id, song.title, e)}
                      disabled={deleting === song.id}
                      className="text-on-surface-variant hover:text-error transition-colors disabled:opacity-50"
                      title="删除"
                    >
                      <span className="material-symbols-outlined text-sm">{deleting === song.id ? "hourglass_empty" : "delete"}</span>
                    </button>
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
          <span className="text-[10px] font-bold">我的作品</span>
        </Link>
        <span className="flex flex-col items-center gap-1 text-white/20 cursor-not-allowed">
          <span className="material-symbols-outlined">library_music</span>
          <span className="text-[10px] font-medium">音乐库</span>
        </span>
        <span className="flex flex-col items-center gap-1 text-white/20 cursor-not-allowed">
          <span className="material-symbols-outlined">settings_voice</span>
          <span className="text-[10px] font-medium">语音模型</span>
        </span>
        <span className="flex flex-col items-center gap-1 text-white/20 cursor-not-allowed">
          <span className="material-symbols-outlined">mic_external_on</span>
          <span className="text-[10px] font-medium">工作室</span>
        </span>
      </footer>

      {/* Add Song Dialog */}
      <dialog ref={dialogRef} className="rounded-2xl p-0 backdrop:bg-black/60 bg-surface-container-low border border-white/10 text-on-surface">
        <div className="p-6 w-full max-w-[480px] max-h-[80vh] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">添加新歌</h2>
            <button
              onClick={handleDialogClose}
              className="text-on-surface-variant hover:text-white transition-colors"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-white/10 mb-4">
            <button
              onClick={() => setDialogTab("search")}
              className={`flex-1 pb-2 text-sm font-bold transition-colors ${
                dialogTab === "search"
                  ? "text-ember border-b-2 border-ember"
                  : "text-on-surface-variant hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-sm align-middle mr-1">search</span>
              搜索歌曲
            </button>
            <button
              onClick={() => setDialogTab("upload")}
              className={`flex-1 pb-2 text-sm font-bold transition-colors ${
                dialogTab === "upload"
                  ? "text-ember border-b-2 border-ember"
                  : "text-on-surface-variant hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-sm align-middle mr-1">upload_file</span>
              上传文件
            </button>
          </div>

          {/* Search Tab */}
          {dialogTab === "search" && (
            <div className="flex-1 overflow-y-auto min-h-0">
              {importing ? (
                <div className="py-12 flex flex-col items-center gap-4">
                  <span className="material-symbols-outlined text-4xl text-ember animate-pulse">downloading</span>
                  <p className="font-bold">{importing}</p>
                  {importProgress && (
                    <>
                      <div className="w-full max-w-xs h-2 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className="h-full bg-ember rounded-full transition-all duration-300"
                          style={{ width: `${importProgress.pct}%` }}
                        />
                      </div>
                      <p className="text-xs text-on-surface-variant">{importProgress.message}</p>
                    </>
                  )}
                </div>
              ) : (
                <>
                  <div className="relative mb-4">
                    <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
                    <input
                      className="w-full bg-surface-container border-none rounded-lg pl-10 pr-4 py-2.5 text-on-surface focus:ring-2 focus:ring-ember/40 transition-all"
                      placeholder="搜索歌曲名或歌手..."
                      value={searchQuery}
                      onChange={(e) => handleSearchInput(e.target.value)}
                      autoFocus
                    />
                  </div>
                  {searchError && (
                    <div className="flex items-center gap-2 p-4 rounded-lg bg-error/10 text-error mb-4">
                      <span className="material-symbols-outlined text-lg">cloud_off</span>
                      <p className="text-sm font-medium">{searchError}</p>
                    </div>
                  )}
                  {searching && (
                    <div className="flex justify-center py-8">
                      <span className="material-symbols-outlined text-3xl text-ember animate-pulse">hourglass_empty</span>
                    </div>
                  )}
                  {!searching && !searchError && searchResults.length === 0 && searchQuery && (
                    <p className="text-center text-on-surface-variant py-8">没有找到相关歌曲</p>
                  )}
                  {!searching && !searchError && searchResults.length === 0 && !searchQuery && (
                    <p className="text-center text-on-surface-variant py-8">输入关键词搜索歌曲，支持网易云、QQ、酷狗等平台</p>
                  )}
                  <div className="space-y-2">
                    {searchResults.map((song) => (
                      <div
                        key={`${song.source}-${song.id}`}
                        className="flex items-center gap-3 p-3 rounded-lg bg-surface-container hover:bg-surface-variant transition-colors group"
                      >
                        {song.cover_url ? (
                          <img
                            src={song.cover_url}
                            alt=""
                            className="w-10 h-10 rounded object-cover flex-shrink-0"
                            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
                          />
                        ) : (
                          <div className="w-10 h-10 rounded bg-surface-container-high flex items-center justify-center flex-shrink-0">
                            <span className="material-symbols-outlined text-lg text-on-surface-variant">music_note</span>
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-sm truncate">{song.name}</p>
                          <div className="flex items-center gap-2">
                            <p className="text-xs text-on-surface-variant truncate">{song.artist}</p>
                            {song.duration > 0 && (
                              <span className="text-[10px] text-on-surface-variant/50 flex-shrink-0">
                                {Math.floor(song.duration / 60)}:{String(song.duration % 60).padStart(2, "0")}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1 flex-shrink-0">
                          {song.platforms.slice(0, 3).map((p) => (
                            <span
                              key={p.source}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-on-surface-variant"
                            >
                              {p.name}
                            </span>
                          ))}
                          {song.platforms.length > 3 && (
                            <span className="text-[10px] text-on-surface-variant">+{song.platforms.length - 3}</span>
                          )}
                        </div>
                        <button
                          onClick={() => handleImport(song)}
                          disabled={!!importing}
                          className="bg-ember text-on-primary-fixed px-3 py-1.5 rounded text-xs font-bold transition-opacity active:scale-95 disabled:opacity-50"
                        >
                          导入
                        </button>
                      </div>
                    ))}
                  </div>
                  {/* Copyright notice */}
                  <p className="text-[10px] text-on-surface-variant/60 text-center mt-4 pb-2">
                    仅供个人翻唱创作使用，请勿用于商业用途
                  </p>
                </>
              )}
            </div>
          )}

          {/* Upload Tab */}
          {dialogTab === "upload" && (
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
          )}
        </div>
      </dialog>
    </div>
  );
}
