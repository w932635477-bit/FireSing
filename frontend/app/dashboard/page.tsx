"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import {
  listSongs,
  uploadSong,
  deleteSong,
  searchMusic,
  importMusic,
  checkMusicExisting,
  connectImportProgress,
  clearToken,
  AppError,
  type Song,
  type MusicSearchSong,
  type MusicImportProgress,
} from "@/lib/api";
import { useToast } from "@/components/Toast";
import { ConfirmDialog } from "@/components/ConfirmDialog";

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

export default function DashboardPage() {
  const { addToast } = useToast();
  const { user, logout } = useAuth();
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; title: string } | null>(null);
  const [apiError, setApiError] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  // Music search state
  const [dialogTab, setDialogTab] = useState<"search" | "upload">("search");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<MusicSearchSong[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [importing, setImporting] = useState<string | null>(null);
  const [importProgress, setImportProgress] = useState<MusicImportProgress | null>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(null);

  async function handleDelete(songId: string, songTitle: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDeleteConfirm({ id: songId, title: songTitle });
  }

  async function confirmDelete() {
    if (!deleteConfirm) return;
    setDeleting(deleteConfirm.id);
    setDeleteConfirm(null);
    try { await deleteSong(deleteConfirm.id); await load(); }
    catch (e) { addToast("error", `删除失败: ${e instanceof Error ? e.message : "请重试"}`); }
    finally { setDeleting(null); }
  }

  const load = useCallback(async () => {
    try {
      const data = await listSongs();
      setSongs(data.songs || []);
    } catch {
      setSongs([]);
      setApiError(true);
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
        if (e instanceof AppError && e.status === 503) {
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
    try {
      const { exists } = await checkMusicExisting(song.source, song.id);
      if (exists) {
        addToast("warning", "这首歌已经导入过了");
        return;
      }
    } catch {}

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
    <div className="min-h-screen bg-surface-container-lowest text-on-surface pb-20 md:pb-0">
      {/* Top Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-neutral-950/80 backdrop-blur-xl shadow-[0_20px_50px_rgba(89,23,0,0.06)] flex justify-between items-center px-6 md:px-8 h-16">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-2xl font-black text-primary tracking-tighter">FireSing</Link>
          <div className="hidden md:flex gap-6 items-center">
            <Link href="/" className="text-neutral-400 hover:text-neutral-200 transition-colors duration-300">首页</Link>
            <Link href="/dashboard" className="text-primary font-bold border-b-2 border-primary pb-1">我的作品</Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={openDialog}
            className="bg-primary text-on-primary-fixed px-4 py-2 rounded-xl text-sm font-bold hover:scale-95 transition-transform flex items-center gap-2 shadow-[0_0_20px_rgba(255,107,53,0.2)]"
          >
            <span className="material-symbols-outlined text-sm">add</span>
            添加新歌
          </button>
          <Link href={user?.authenticated ? "/pricing" : "/login"} className="w-8 h-8 rounded-full overflow-hidden bg-surface-container-highest border border-white/5 hover:border-white/20 transition-colors flex items-center justify-center" title={user?.authenticated ? "账户" : "登录"}>
            {user?.authenticated ? (
              <span className="text-xs font-bold text-primary">{user.nickname?.[0] || "U"}</span>
            ) : (
              <div className="w-full h-full bg-gradient-to-tr from-primary to-tertiary opacity-80" />
            )}
          </Link>
          {user?.authenticated && (
            <button
              onClick={() => { logout(); }}
              className="text-neutral-500 hover:text-white transition-colors text-xs"
              title="退出登录"
            >
              <span className="material-symbols-outlined text-lg">logout</span>
            </button>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-24 px-6 md:px-12 max-w-7xl mx-auto">
        {/* Trial mode banner */}
        {!user?.authenticated && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-between gap-4">
            <p className="text-sm text-on-surface font-medium">
              <span className="text-primary font-bold">试用模式</span> — 登录后可保存作品和充值
            </p>
            <Link href="/login" className="text-xs font-bold text-primary px-3 py-1.5 bg-primary/10 rounded-lg hover:bg-primary/20 transition-colors flex-shrink-0">
              登录
            </Link>
          </div>
        )}
        {/* Header */}
        <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="relative">
            <h1 className="text-4xl md:text-5xl font-black tracking-tight -ml-1">我的作品</h1>
            <div className="h-1 w-12 bg-primary mt-2" />
          </div>
          {songs.length > 0 && (
            <div className="relative w-full md:w-80 group">
              <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
              <input
                className="w-full bg-surface-container-low border-none rounded-xl pl-12 pr-4 py-3 text-on-surface placeholder:text-on-surface-variant focus:ring-0 group-hover:bg-surface-container-high transition-colors"
                placeholder="搜索作品..."
                type="text"
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
              />
              <div className="absolute bottom-0 left-0 w-full h-0.5 bg-primary scale-x-0 group-focus-within:scale-x-100 transition-transform origin-left" />
            </div>
          )}
        </header>

        {/* Song Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-32">
            <span className="material-symbols-outlined text-5xl text-primary animate-pulse">hourglass_empty</span>
          </div>
        ) : songs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 text-center">
            {apiError && (
              <div className="mb-6 px-4 py-3 rounded-xl bg-error/10 text-error text-sm max-w-md">
                无法连接到服务器，请确认后端服务已启动。
              </div>
            )}
            <div className="w-24 h-24 bg-surface-container-high rounded-full flex items-center justify-center mb-6">
              <span className="material-symbols-outlined text-5xl text-primary">library_music</span>
            </div>
            <h2 className="text-2xl font-bold mb-2">还没有作品</h2>
            <p className="text-neutral-500 mb-8 max-w-xs">点击右上角上传第一首歌，开始您的创作之旅</p>
            <button
              onClick={openDialog}
              className="bg-surface-container-high border border-white/10 px-6 py-3 rounded-xl font-bold hover:bg-surface-container-highest active:scale-[0.98] transition-all"
            >
              添加新歌
            </button>
          </div>
        ) : (
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 pb-12">
            {songs
              .filter((s) => !filterQuery || s.title.toLowerCase().includes(filterQuery.toLowerCase()))
              .map((song, index) => (
                <Link
                  key={song.id}
                  href={`/songs/${song.id}`}
                  className="group relative bg-surface-container-low rounded-2xl overflow-hidden cursor-pointer transition-all duration-500 hover:bg-surface-container-high"
                >
                  <div className="aspect-video overflow-hidden relative">
                    <Image
                      src={getCover(song.title)}
                      alt={song.title}
                      fill
                      priority={index < 3}
                      className="object-cover transition-transform duration-700 group-hover:scale-110"
                      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                    {/* Status dot */}
                    {song.status === "done" && (
                      <div className="absolute top-4 right-4 w-3 h-3 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.6)]" />
                    )}
                    {song.status === "error" && (
                      <div className="absolute top-4 right-4 w-3 h-3 rounded-full bg-error shadow-[0_0_10px_rgba(255,113,108,0.6)]" />
                    )}
                    {song.status !== "uploaded" && song.status !== "done" && song.status !== "error" && (
                      <div className="absolute top-4 right-4 w-3 h-3 rounded-full bg-orange-500 animate-pulse shadow-[0_0_12px_rgba(249,115,22,0.8)]" />
                    )}
                    {song.status === "uploaded" && (
                      <div className="absolute top-4 right-4 w-3 h-3 rounded-full bg-neutral-500" />
                    )}
                    {/* Delete button */}
                    <button
                      onClick={(e) => handleDelete(song.id, song.title, e)}
                      disabled={deleting === song.id}
                      className="absolute top-4 left-4 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-md p-1.5 rounded-lg text-white hover:text-error disabled:opacity-50"
                      title="删除"
                    >
                      <span className="material-symbols-outlined text-sm">{deleting === song.id ? "hourglass_empty" : "close"}</span>
                    </button>
                    {/* Hover play icon */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="material-symbols-outlined text-4xl text-white/90" style={{ fontVariationSettings: '"FILL" 1' }}>play_circle</span>
                    </div>
                  </div>
                  <div className="p-6">
                    <h3 className="text-xl font-bold tracking-tight text-on-surface truncate">{song.title}</h3>
                    <p className="text-neutral-500 text-sm mt-1">
                      {song.status === "done" ? "已完成" : song.status === "error" ? "解析失败，请重试" : ["uploaded"].includes(song.status) ? "已上传" : "处理中..."}
                    </p>
                  </div>
                </Link>
              ))}
          </section>
        )}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-16 flex justify-around items-center px-4 bg-black z-50 border-t border-white/5">
        <Link href="/" className="flex flex-col items-center justify-center text-neutral-500 p-2 hover:bg-neutral-800 transition-colors">
          <span className="material-symbols-outlined">home</span>
          <span className="text-xs font-medium">首页</span>
        </Link>
        <Link href="/dashboard" className="flex flex-col items-center justify-center text-primary bg-neutral-900/50 rounded-lg p-2">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: '"FILL" 1' }}>library_music</span>
          <span className="text-xs font-medium">我的作品</span>
        </Link>
        <Link href="/pricing" className="flex flex-col items-center justify-center text-neutral-500 p-2 hover:bg-neutral-800 transition-colors">
          <span className="material-symbols-outlined">account_balance_wallet</span>
          <span className="text-xs font-medium">充值</span>
        </Link>
      </nav>

      {/* 添加新歌 Dialog */}
      <dialog ref={dialogRef} className="rounded-2xl p-0 backdrop:bg-black/60 backdrop:backdrop-blur-md bg-surface-container-high border border-white/5 text-on-surface">
        <div className="p-6 w-full max-w-[480px] max-h-[80vh] flex flex-col">
          <div className="flex items-center justify-between p-6 border-b border-white/5">
            <h2 className="text-xl font-bold">添加新歌</h2>
            <button onClick={handleDialogClose} className="text-neutral-500 hover:text-white transition-colors">
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex p-2 bg-surface-container-low m-6 mb-4 rounded-xl">
            <button
              onClick={() => setDialogTab("search")}
              className={`flex-1 py-2 text-sm font-bold rounded-lg transition-colors ${
                dialogTab === "search" ? "bg-surface-container-highest text-primary" : "text-neutral-500 hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-sm align-middle mr-1">search</span>
              搜索歌曲
            </button>
            <button
              onClick={() => setDialogTab("upload")}
              className={`flex-1 py-2 text-sm font-bold rounded-lg transition-colors ${
                dialogTab === "upload" ? "bg-surface-container-highest text-primary" : "text-neutral-500 hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-sm align-middle mr-1">upload_file</span>
              上传文件
            </button>
          </div>

          {/* Search Tab */}
          {dialogTab === "search" && (
            <div className="flex-1 overflow-y-auto min-h-0 px-6 pb-6 space-y-4">
              {importing ? (
                <div className="py-12 flex flex-col items-center gap-4">
                  <span className="material-symbols-outlined text-4xl text-primary animate-pulse">downloading</span>
                  <p className="font-bold">{importing}</p>
                  {importProgress && (
                    <>
                      <div className="w-full max-w-xs h-2 rounded-full bg-white/10 overflow-hidden">
                        <div className="h-full bg-primary rounded-full transition-all duration-300" style={{ width: `${importProgress.pct}%` }} />
                      </div>
                      <p className="text-xs text-neutral-500">{importProgress.message}</p>
                    </>
                  )}
                </div>
              ) : (
                <>
                  <div className="relative">
                    <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500">search</span>
                    <input
                      className="w-full bg-surface-container-lowest border-none rounded-xl pl-12 pr-4 py-4 text-on-surface placeholder:text-neutral-600 focus:outline-none"
                      placeholder="搜索歌曲名或歌手..."
                      value={searchQuery}
                      onChange={(e) => handleSearchInput(e.target.value)}
                      autoFocus
                    />
                  </div>
                  {searchError && (
                    <div className="flex items-center gap-2 p-4 rounded-xl bg-error/10 text-error">
                      <span className="material-symbols-outlined text-lg">cloud_off</span>
                      <p className="text-sm font-medium">{searchError}</p>
                    </div>
                  )}
                  {searching && (
                    <div className="flex justify-center py-8">
                      <span className="material-symbols-outlined text-3xl text-primary animate-pulse">hourglass_empty</span>
                    </div>
                  )}
                  {!searching && !searchError && searchResults.length === 0 && searchQuery && (
                    <p className="text-center text-neutral-500 py-8">没有找到相关歌曲</p>
                  )}
                  {!searching && !searchError && searchResults.length === 0 && !searchQuery && (
                    <p className="text-center text-neutral-500 py-8">输入关键词搜索歌曲，支持网易云、QQ、酷狗等平台</p>
                  )}
                  <div className="space-y-2">
                    {searchResults.map((song) => (
                      <div key={`${song.source}-${song.id}`} className="bg-surface-container-low p-4 rounded-xl flex items-center justify-between hover:bg-surface-container-highest transition-colors">
                        <div className="flex items-center gap-4">
                          {song.cover_url ? (
                            <img src={song.cover_url} alt="" className="w-12 h-12 rounded-lg object-cover flex-shrink-0" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }} />
                          ) : (
                            <div className="w-12 h-12 rounded-lg bg-surface-container-highest flex items-center justify-center flex-shrink-0">
                              <span className="material-symbols-outlined text-lg text-neutral-500">music_note</span>
                            </div>
                          )}
                          <div>
                            <h4 className="font-bold text-on-surface">{song.name}</h4>
                            <div className="flex items-center gap-2 text-xs text-neutral-500">
                              <span>{song.artist}</span>
                              {song.duration > 0 && (
                                <span className="flex-shrink-0">{Math.floor(song.duration / 60)}:{String(song.duration % 60).padStart(2, "0")}</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {song.platforms.slice(0, 3).map((p) => (
                            <span key={`${p.source}-${p.id}`} className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-neutral-400">
                              {p.source_name || p.source}
                            </span>
                          ))}
                          <button
                            onClick={() => handleImport(song)}
                            disabled={!!importing}
                            className="bg-primary-container text-on-primary-fixed px-4 py-2 rounded-lg text-xs font-bold hover:bg-primary transition-all disabled:opacity-50"
                          >
                            导入
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-[10px] text-neutral-600 text-center mt-4 pb-2">
                    仅供个人翻唱创作使用，请勿用于商业用途
                  </p>
                </>
              )}
            </div>
          )}

          {/* Upload Tab */}
          {dialogTab === "upload" && (
            <form onSubmit={handleUpload} className="px-6 pb-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-neutral-500 uppercase tracking-widest mb-2">音频文件 *</label>
                <input
                  name="audio"
                  type="file"
                  accept=".mp3,.wav,.flac"
                  required
                  className="block w-full text-sm text-neutral-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary/20 file:text-primary hover:file:bg-primary/30 transition-colors"
                />
                <p className="text-xs text-neutral-600 mt-1">支持 MP3/WAV/FLAC，最大 50MB</p>
              </div>
              <div>
                <label className="block text-xs font-bold text-neutral-500 uppercase tracking-widest mb-2">LRC 歌词文件（可选）</label>
                <input
                  name="lrc"
                  type="file"
                  accept=".lrc,.txt"
                  className="block w-full text-sm text-neutral-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-surface-container-highest file:text-neutral-300 hover:file:bg-surface-container-high transition-colors"
                />
              </div>
              <button
                type="submit"
                disabled={uploading}
                className="w-full py-3 bg-primary text-on-primary-fixed rounded-xl font-bold hover:opacity-90 disabled:opacity-50 active:scale-[0.98] transition-all"
              >
                {uploading ? "上传中..." : "上传"}
              </button>
            </form>
          )}
        </div>
      </dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteConfirm !== null}
        title="删除歌曲"
        message={`确定删除「${deleteConfirm?.title ?? ""}」？此操作不可恢复。`}
        confirmLabel="删除"
        cancelLabel="取消"
        variant="danger"
        onConfirm={confirmDelete}
        onCancel={() => setDeleteConfirm(null)}
      />
    </div>
  );
}
