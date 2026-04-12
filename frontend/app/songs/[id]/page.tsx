"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getSong,
  getSegments,
  listVoices,
  uploadVoice,
  getOutputs,
  startProcess,
  uploadMonologueAudio,
  uploadLrc,
  statusLabel,
  type Song,
  type Segment,
  type VoiceModel,
  type Output,
  type ProcessRequest,
} from "@/lib/api";
import { useToast } from "@/components/Toast";
import { ConfirmDialog } from "@/components/ConfirmDialog";

const VOICE_COLORS = [
  { chip: "voice-chip-red", dot: "bg-primary", label: "珊瑚红" },
  { chip: "voice-chip-green", dot: "bg-success", label: "薄荷绿" },
  { chip: "voice-chip-blue", dot: "bg-secondary", label: "天蓝色" },
  { chip: "voice-chip-gray", dot: "bg-on-surface-variant", label: "灰绿色" },
  { chip: "voice-chip-purple", dot: "bg-purple-400", label: "紫罗兰" },
  { chip: "voice-chip-orange", dot: "bg-orange-400", label: "橘黄色" },
  { chip: "voice-chip-pink", dot: "bg-pink-400", label: "粉红色" },
  { chip: "voice-chip-teal", dot: "bg-teal-400", label: "青碧色" },
];

export default function SongDetailPage() {
  const params = useParams();
  const router = useRouter();
  const songId = params.id as string;
  const { addToast } = useToast();
  const [song, setSong] = useState<Song | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [voices, setVoices] = useState<VoiceModel[]>([]);
  const [outputs, setOutputs] = useState<Output[]>([]);
  const [loading, setLoading] = useState(true);

  const [gpuOnline, setGpuOnline] = useState(true);
  const [monologueText, setMonologueText] = useState("");
  const [monologueMode, setMonologueMode] = useState<"text" | "record">("text");
  const [monologuePosition, setMonologuePosition] = useState<"beginning" | "end" | "interlude">("beginning");
  const [monologueFile, setMonologueFile] = useState<File | null>(null);
  const [monologueUploading, setMonologueUploading] = useState(false);
  const [outputFormat, setOutputFormat] = useState<"video" | "audio" | "video_subtitled">("video");
  const [enableChorus, setEnableChorus] = useState(true);
  const [chorusVoiceCount, setChorusVoiceCount] = useState(5);
  const [voiceUploading, setVoiceUploading] = useState(false);
  const [showVoiceUpload, setShowVoiceUpload] = useState(false);
  const [selectedVoiceIds, setSelectedVoiceIds] = useState<string[]>([]);
  const [processConfirm, setProcessConfirm] = useState<string | null>(null);
  const [pendingProcessData, setPendingProcessData] = useState<{ pool: string[]; req: ProcessRequest } | null>(null);
  const [lrcUploading, setLrcUploading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [songData, segData, voiceData] = await Promise.all([
        getSong(songId),
        getSegments(songId).catch(() => ({ segments: [] })),
        listVoices(),
      ]);
      setSong(songData);
      setSegments(segData.segments || []);
      setVoices(voiceData.voices || []);
      if (songData.status === "done") {
        const outData = await getOutputs(songId).catch(() => ({ outputs: [] }));
        setOutputs(outData.outputs || []);
      }
    } catch (e) {
      console.error("Failed to load song:", e);
      setSong(null);
    } finally {
      setLoading(false);
    }
  }, [songId]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    let mounted = true;
    let interval: ReturnType<typeof setInterval>;
    async function check() {
      try {
        const resp = await fetch("/api/health/gpu");
        if (!mounted) return;
        if (resp.ok) {
          const data = await resp.json();
          setGpuOnline(data.status === "ok");
        } else { setGpuOnline(false); }
      } catch { if (mounted) setGpuOnline(false); }
    }
    check();
    interval = setInterval(check, 30000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  function toggleVoice(voiceId: string) {
    setSelectedVoiceIds((prev) =>
      prev.includes(voiceId) ? prev.filter((id) => id !== voiceId) : [...prev, voiceId]
    );
  }

  async function handleUploadVoice(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const pth = fd.get("pth_file") as File;
    const idx = fd.get("index_file") as File;
    const name = fd.get("name") as string;
    if (!pth || !name) { addToast("warning", "请填写音色名称并选择 .pth 文件"); return; }
    setVoiceUploading(true);
    try { await uploadVoice(pth, idx?.size > 0 ? idx : null, name); await load(); setShowVoiceUpload(false); }
    catch (e) { addToast("error", `音色上传失败: ${e instanceof Error ? e.message : "请重试"}`); }
    finally { setVoiceUploading(false); }
  }

  async function handleStartProcess() {
    if (selectedVoiceIds.length === 0) { addToast("warning", "请先选择至少一个音色"); return; }

    const voiceNames = selectedVoiceIds.map(id => voices.find(v => v.id === id)?.name || id).join(", ");
    const fmt = outputFormat === "video" ? "竖版视频" : outputFormat === "audio" ? "纯音频" : "字幕视频";
    const summary = `音色: ${voiceNames}\n输出: ${fmt}${enableChorus ? ` · ${chorusVoiceCount}声部合唱` : ""}${monologueText ? ` · 含独白` : ""}`;

    const req: ProcessRequest = {
      voice_pool: selectedVoiceIds,
      strategy: "round-robin",
      monologue_text: monologueMode === "text" && monologueText ? monologueText : undefined,
      monologue_position: monologuePosition,
      output_format: outputFormat,
      enable_chorus: enableChorus,
      chorus_voice_count: chorusVoiceCount,
    };

    setPendingProcessData({ pool: selectedVoiceIds, req });
    setProcessConfirm(summary);
  }

  async function confirmStartProcess() {
    setProcessConfirm(null);
    if (!pendingProcessData) return;

    if (monologueMode === "record" && monologueFile) {
      setMonologueUploading(true);
      try { await uploadMonologueAudio(songId, monologueFile); }
      catch (e) { setMonologueUploading(false); setPendingProcessData(null); return addToast("error", `独白上传失败: ${e instanceof Error ? e.message : "请重试"}`); }
      finally { setMonologueUploading(false); }
    }

    try { await startProcess(songId, pendingProcessData.req); router.push(`/songs/${songId}/process`); }
    catch (e) { addToast("error", `处理启动失败: ${e instanceof Error ? e.message : "请重试"}`); }
    finally { setPendingProcessData(null); }
  }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <span className="material-symbols-outlined text-5xl text-primary animate-pulse">hourglass_empty</span>
    </div>
  );
  if (!song) return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <span className="material-symbols-outlined text-4xl text-error">error</span>
      <p className="text-on-surface-variant">歌曲不存在或加载失败</p>
      <Link href="/dashboard" className="text-primary font-bold text-sm hover:underline">返回我的作品</Link>
    </div>
  );

  const hasSegments = segments.length > 0;
  const canProcess = selectedVoiceIds.length > 0 && !["separating", "segmenting", "assigning", "converting", "harmony", "chorus", "monologue", "mixing", "video"].includes(song.status);
  const isProcessing = ["separating", "segmenting", "assigning", "converting", "harmony", "chorus", "monologue", "mixing", "video"].includes(song.status);
  const isDone = song.status === "done";
  const isError = song.status === "error";

  const currentStep = selectedVoiceIds.length === 0 ? 1 : 2;

  return (
    <div className="min-h-screen bg-surface-container-lowest text-on-surface pb-32" style={{ fontFamily: "'Inter', 'PingFang SC', sans-serif" }}>
      {/* Top Nav */}
      <header className="fixed top-0 w-full z-50 bg-neutral-950/80 backdrop-blur-xl shadow-[0_20px_50px_rgba(89,23,0,0.06)]">
        <div className="max-w-3xl mx-auto h-16 flex items-center justify-between px-6">
          <div className="flex items-center gap-2 text-neutral-400 hover:text-neutral-200 transition-colors duration-300 cursor-pointer active:scale-95">
            <Link href="/dashboard" className="flex items-center gap-1">
              <span className="material-symbols-outlined">arrow_back</span>
              <span className="font-medium">我的作品</span>
            </Link>
          </div>
          <h1 className="text-on-surface font-bold text-lg tracking-tight -ml-8 truncate max-w-[200px]">{song.title}</h1>
          <div className="flex items-center gap-3">
            <span className={`px-2 py-0.5 text-[10px] font-bold rounded-sm tracking-wider ${
              isDone ? "bg-green-500/20 text-green-400 border border-green-500/30" : isProcessing ? "bg-primary/20 text-primary border border-primary/30" : song.status === "error" ? "bg-error/20 text-error border border-error/30" : "bg-surface-container-highest text-on-surface-variant border border-outline-variant/30"
            }`}>
              {statusLabel(song.status)}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto pt-24 px-6 space-y-12">
        {/* Step Indicator */}
        <div className="relative flex justify-between items-center px-2">
          <div className="absolute top-1/2 left-0 w-full h-px -z-10" style={{ background: "linear-gradient(90deg, transparent 0%, #262528 50%, transparent 100%)" }} />
          {[
            { num: 1, label: "选音色", done: selectedVoiceIds.length > 0 },
            { num: 2, label: "生成", done: isDone },
          ].map((step) => (
            <div key={step.num} className="flex flex-col items-center gap-2">
              <div className={`w-10 h-10 md:w-8 md:h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                step.done
                  ? "bg-primary text-on-primary-fixed shadow-[0_0_12px_rgba(255,107,53,0.2)]"
                  : currentStep === step.num
                    ? "bg-primary text-on-primary-fixed shadow-[0_0_12px_rgba(255,107,53,0.2)]"
                    : "bg-surface-container-highest border border-outline-variant/30 text-on-surface-variant"
              }`}>
                {step.done ? <span className="material-symbols-outlined text-lg md:text-base" style={{ fontVariationSettings: '"FILL" 1' }}>check_circle</span> : step.num}
              </div>
              <span className={`text-xs font-bold ${step.done ? "text-primary" : currentStep === step.num ? "text-primary" : "text-on-surface-variant"}`}>{step.label}</span>
            </div>
          ))}
        </div>

        {/* Processing state */}
        {isProcessing && (
          <div className="bg-surface-container-low rounded-xl p-6 text-center border border-primary/20">
            <span className="material-symbols-outlined text-3xl text-primary animate-pulse mb-2 block">progress_activity</span>
            <p className="text-on-surface font-bold mb-1">正在处理中</p>
            <Link href={`/songs/${songId}/process`} className="text-sm text-primary underline">
              查看进度
            </Link>
          </div>
        )}

        {/* Error state with retry */}
        {isError && (
          <div className="bg-surface-container-low rounded-xl p-6 border border-error/20">
            <div className="flex items-center gap-3 mb-3">
              <span className="material-symbols-outlined text-3xl text-error">error</span>
              <div>
                <p className="text-on-surface font-bold">处理失败</p>
                {song.error_message && (
                  <p className="text-sm text-on-surface-variant mt-1">{song.error_message}</p>
                )}
              </div>
            </div>
            <button
              onClick={() => {
                setSong({ ...song, status: "uploaded", error_message: undefined });
              }}
              className="bg-primary text-on-primary-fixed px-6 py-2 rounded-xl text-sm font-bold active:scale-95 transition-transform"
            >
              重新设置并重试
            </button>
          </div>
        )}

        {/* Done state: show outputs */}
        {isDone && outputs.length > 0 && (
          <section className="mb-8">
            <h2 className="text-sm font-bold text-on-surface-variant mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-base">download</span>
              输出文件
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {outputs.map((out) => (
                <div key={out.id} className="bg-surface-container-low rounded-xl overflow-hidden border border-white/5">
                  {out.format === "video" ? (
                    <video controls className="w-full" src={out.file_url}>
                      <track kind="captions" />
                    </video>
                  ) : (
                    <div className="p-4"><audio controls className="w-full" src={out.file_url} /></div>
                  )}
                  <div className="flex items-center justify-between p-4 pt-3">
                    <span className="text-xs text-on-surface-variant">
                      {out.format === "video" ? "MP4" : "WAV"}
                      {out.duration && ` · ${out.duration.toFixed(0)}s`}
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => { navigator.clipboard.writeText(window.location.origin + out.file_url); addToast("success", "链接已复制"); }}
                        className="px-3 py-1.5 bg-surface-container-highest text-on-surface rounded-lg text-xs font-bold hover:bg-surface-bright transition-colors flex items-center gap-1"
                      >
                        <span className="material-symbols-outlined text-xs">link</span>
                        复制链接
                      </button>
                      <a href={out.file_url} download className="px-3 py-1.5 bg-primary text-black rounded-lg text-xs font-bold active:scale-95 transition-transform">
                        下载
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {/* Next actions after completion */}
            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <Link
                href="/dashboard"
                prefetch={false}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-surface-container-high rounded-xl text-sm font-bold hover:bg-surface-bright transition-colors border border-white/5"
              >
                <span className="material-symbols-outlined text-base">add</span>
                再来一首
              </Link>
              <button
                onClick={() => load()}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-surface-container-high rounded-xl text-sm font-bold hover:bg-surface-bright transition-colors border border-white/5"
              >
                <span className="material-symbols-outlined text-base">refresh</span>
                刷新状态
              </button>
            </div>
          </section>
        )}

        {/* Auto segmentation notice + LRC upload */}
        {!isProcessing && !isDone && (
          <section className="space-y-4">
            <div className="p-4 bg-primary/5 rounded-xl border border-primary/10 flex items-center gap-3">
              <span className="material-symbols-outlined text-primary text-xl">auto_awesome</span>
              <div className="flex-1">
                <p className="text-xs text-on-surface-variant">智能分段：处理时自动检测人声段落，无需上传歌词文件</p>
                <p className="text-xs text-on-surface-variant mt-1 opacity-60">上传 LRC 歌词文件可以获得带歌词文字的分段（替代默认的"Segment N"标签）</p>
              </div>
            </div>
            {/* LRC Upload */}
            {!song.lrc_path && (
              <div className="p-4 bg-surface-container-low rounded-xl border border-white/5">
                <p className="text-xs font-bold text-on-surface-variant mb-2">上传歌词文件（可选，获得更好的分段文字）</p>
                <div className="flex gap-2">
                  <input
                    type="file"
                    accept=".lrc,.txt"
                    id="lrc-upload"
                    className="hidden"
                    onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      setLrcUploading(true);
                      try {
                        await uploadLrc(songId, file);
                        addToast("success", "歌词上传成功，已更新分段");
                        await load();
                      } catch (err) {
                        addToast("error", `歌词上传失败: ${err instanceof Error ? err.message : "请重试"}`);
                      } finally {
                        setLrcUploading(false);
                      }
                    }}
                  />
                  <button
                    onClick={() => document.getElementById("lrc-upload")?.click()}
                    disabled={lrcUploading}
                    className="px-4 py-2 bg-surface-container-highest text-on-surface text-xs font-bold rounded-lg hover:bg-surface-bright transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined text-sm">{lrcUploading ? "hourglass_empty" : "upload_file"}</span>
                    {lrcUploading ? "上传中..." : "选择 LRC 文件"}
                  </button>
                </div>
              </div>
            )}
            {song.lrc_path && (
              <div className="p-3 bg-success/5 rounded-xl border border-success/10 flex items-center gap-2">
                <span className="material-symbols-outlined text-success text-base" style={{ fontVariationSettings: '"FILL" 1' }}>check_circle</span>
                <p className="text-xs text-success font-medium">已上传歌词文件，分段包含歌词文字</p>
              </div>
            )}
          </section>
        )}

        {/* Step 1: Select Voice Models */}
        {!isProcessing && !isDone && (
          <section className="space-y-4">
            <div className="flex justify-between items-end">
              <h2 className="text-xl font-bold tracking-tight -ml-2 text-on-surface">选择音色{selectedVoiceIds.length > 0 && <span className="text-sm font-normal text-on-surface-variant ml-2">已选 {selectedVoiceIds.length} 个</span>}</h2>
              <button
                onClick={() => setShowVoiceUpload(!showVoiceUpload)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container-highest rounded-lg text-xs font-bold text-on-surface-variant hover:bg-surface-bright transition-colors"
              >
                <span className="material-symbols-outlined text-base">upload_file</span>
                <span>导入模型</span>
              </button>
            </div>

            {showVoiceUpload && (
              <form onSubmit={handleUploadVoice} className="p-6 bg-surface-container-low rounded-xl space-y-4">
                <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest">导入自定义 RVC 模型</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-on-surface-variant ml-1">音色名称</label>
                    <input name="name" placeholder="音色名称" required className="w-full bg-surface-container-highest border-none rounded-lg text-sm text-on-surface focus:ring-1 focus:ring-primary placeholder:text-neutral-600 px-4 py-2.5" />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-on-surface-variant ml-1">.pth 文件 *</label>
                    <input name="pth_file" type="file" accept=".pth" required className="w-full text-sm text-on-surface-variant file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-primary/20 file:text-primary" />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-on-surface-variant ml-1">.index 文件</label>
                    <input name="index_file" type="file" accept=".index" className="w-full text-sm text-on-surface-variant file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-surface-container-highest file:text-on-surface-variant" />
                  </div>
                  <div className="flex items-end">
                    <button type="submit" disabled={voiceUploading} className="w-full px-4 py-2.5 bg-primary text-black rounded-lg text-sm font-bold disabled:opacity-50 active:scale-95 transition-transform">
                      {voiceUploading ? "上传中..." : "上传"}
                    </button>
                  </div>
                </div>
              </form>
            )}

            {voices.length === 0 ? (
              <div className="bg-surface-container-low rounded-xl p-6 text-center">
                <span className="material-symbols-outlined text-3xl text-outline-variant mb-2 block">settings_voice</span>
                <p className="text-sm text-on-surface-variant">暂无音色模型</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {voices.map((v, i) => {
                  const selected = selectedVoiceIds.includes(v.id);
                  const color = VOICE_COLORS[i % VOICE_COLORS.length];
                  return (
                    <button
                      key={v.id}
                      onClick={() => toggleVoice(v.id)}
                      className={`p-4 rounded-xl flex items-center gap-3 transition-all text-left ${
                        selected
                          ? "bg-primary/10 border-2 border-primary shadow-[0_0_12px_rgba(255,107,53,0.1)]"
                          : "bg-surface-container-high border-2 border-transparent hover:bg-surface-bright"
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-full ${selected ? color.dot : "bg-surface-container-highest"} flex-shrink-0 flex items-center justify-center transition-colors`}>
                        {selected ? (
                          <span className="material-symbols-outlined text-black text-lg" style={{ fontVariationSettings: '"FILL" 1' }}>check</span>
                        ) : (
                          <span className="material-symbols-outlined text-on-surface-variant text-lg">person</span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className={`text-sm font-bold truncate ${selected ? "text-primary" : "text-on-surface"}`}>{v.name}</p>
                        {selected && <div className={`text-[10px] px-1.5 py-0.5 rounded-full inline-block ${color.chip} mt-0.5`}>{color.label}</div>}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
            {selectedVoiceIds.length === 1 && (
              <p className="text-xs text-on-surface-variant text-center">选择 2 个或更多音色，可以创建接力合唱效果</p>
            )}
          </section>
        )}

        {/* Step 2: Settings + Start */}
        {!isProcessing && !isDone && selectedVoiceIds.length > 0 && (
          <section className="space-y-8">
            <h2 className="text-xl font-bold tracking-tight -ml-2 text-on-surface">渲染设置</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Left Column */}
              <div className="space-y-6">
                {/* Monologue */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-bold">个人独白（可选）</h3>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-${monologueMode === "text" ? "bold text-primary" : "medium text-on-surface-variant"}`}>文字</span>
                      <button onClick={() => setMonologueMode(monologueMode === "text" ? "record" : "text")}
                        className="w-8 h-4 bg-primary rounded-full relative cursor-pointer"
                      >
                        <div className={`absolute top-0.5 w-3 h-3 bg-black rounded-full transition-transform ${monologueMode === "record" ? "right-0.5" : "left-0.5"}`} />
                      </button>
                      <span className={`text-[10px] font-${monologueMode === "record" ? "bold text-primary" : "medium text-on-surface-variant"}`}>录音</span>
                    </div>
                  </div>
                  <div className="p-4 bg-surface-container-low rounded-xl space-y-3">
                    {monologueMode === "text" ? (
                      <textarea value={monologueText} onChange={(e) => setMonologueText(e.target.value)}
                        className="w-full bg-surface-container-high rounded-lg p-3 text-sm text-on-surface focus:ring-1 focus:ring-primary/40 placeholder:text-neutral-600 h-20 resize-none border-0"
                        placeholder="输入独白内容..."
                      />
                    ) : (
                      <div>
                        <input type="file" accept="audio/mp3,audio/wav,audio/ogg,.mp3,.wav,.ogg,.m4a"
                          onChange={(e) => setMonologueFile(e.target.files?.[0] || null)}
                          className="w-full text-sm text-on-surface-variant file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-primary/20 file:text-primary"
                        />
                        {monologueFile && <p className="text-xs text-green-400 mt-1">{monologueFile.name}</p>}
                      </div>
                    )}
                    {(monologueText || monologueMode === "record") && (
                      <div className="flex gap-2">
                        <button onClick={() => setMonologuePosition("beginning")} className={`flex-1 py-2 rounded-lg text-[10px] font-bold ${monologuePosition === "beginning" ? "bg-surface-container-highest border border-primary/30 text-primary" : "bg-surface-container-highest text-on-surface-variant"}`}>片头</button>
                        <button onClick={() => setMonologuePosition("end")} className={`flex-1 py-2 rounded-lg text-[10px] font-bold ${monologuePosition === "end" ? "bg-surface-container-highest border border-primary/30 text-primary" : "bg-surface-container-highest text-on-surface-variant"}`}>片尾</button>
                        <button onClick={() => setMonologuePosition("interlude")} className={`flex-1 py-2 rounded-lg text-[10px] font-bold ${monologuePosition === "interlude" ? "bg-surface-container-highest border border-primary/30 text-primary" : "bg-surface-container-highest text-on-surface-variant"}`}>间奏</button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Chorus */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-bold">合唱效果</h3>
                    {enableChorus && <span className="text-[10px] font-mono text-primary font-bold">{chorusVoiceCount} 人混合</span>}
                  </div>
                  <div className="p-6 bg-surface-container-low rounded-xl space-y-4">
                    <div className="flex items-center gap-4">
                      <span className="text-xs font-bold text-on-surface-variant w-4">2</span>
                      <input type="range" min={2} max={8} value={chorusVoiceCount} onChange={(e) => setChorusVoiceCount(Number(e.target.value))}
                        className="flex-1 accent-primary" />
                      <span className="text-xs font-bold text-on-surface-variant w-4">8</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-on-surface-variant">和声合唱</span>
                      <button onClick={() => setEnableChorus(!enableChorus)}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${enableChorus ? "bg-primary" : "bg-surface-container-highest"}`}
                      >
                        <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-black transition-transform ${enableChorus ? "translate-x-5" : "translate-x-1"}`} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Output Format */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold">输出格式</h3>
                <div className="space-y-3">
                  {([
                    { value: "video" as const, icon: "smartphone", label: "竖版视频", desc: "9:16 · 1080p · 动态背景" },
                    { value: "audio" as const, icon: "headphones", label: "纯音频", desc: "WAV · 48kHz · Lossless" },
                    { value: "video_subtitled" as const, icon: "subtitles", label: "字幕视频", desc: "16:9 · 静态封面 · SRT" },
                  ]).map((fmt) => (
                    <button key={fmt.value} onClick={() => setOutputFormat(fmt.value)}
                      className={`w-full p-4 rounded-xl flex items-center justify-between transition-all ${
                        outputFormat === fmt.value
                          ? "bg-primary/5 border border-primary/20"
                          : "bg-surface-container-low border border-transparent hover:bg-surface-container-high"
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          outputFormat === fmt.value ? "bg-primary/20 text-primary" : "bg-surface-container-highest text-on-surface-variant"
                        }`}>
                          <span className="material-symbols-outlined">{fmt.icon}</span>
                        </div>
                        <div className="text-left">
                          <p className="text-sm font-bold">{fmt.label}</p>
                          <p className="text-[10px] text-on-surface-variant">{fmt.desc}</p>
                        </div>
                      </div>
                      {outputFormat === fmt.value ? (
                        <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: '"FILL" 1' }}>check_circle</span>
                      ) : (
                        <div className="w-5 h-5 rounded-full border-2 border-outline-variant" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Start button */}
            <div className="pt-8">
              <button
                onClick={handleStartProcess}
                disabled={!gpuOnline}
                className="w-full py-5 bg-primary rounded-xl text-on-primary-fixed font-bold text-lg shadow-[0_0_12px_rgba(255,107,53,0.2)] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
              >
                <span className="material-symbols-outlined" style={{ fontVariationSettings: '"FILL" 1' }}>bolt</span>
                <span>{gpuOnline ? "开始处理" : "GPU 离线，无法处理"}</span>
              </button>
              <p className="text-center text-[10px] text-on-surface-variant mt-4 font-medium tracking-widest uppercase">
                {gpuOnline ? "预计耗时 120-180 秒" : "请先启动 AutoDL GPU 服务"}
              </p>
            </div>
          </section>
        )}

        {/* Next step hint */}
        {!isProcessing && !isDone && !canProcess && (
          <div className="text-center py-4">
            <p className="text-sm text-on-surface-variant">
              {selectedVoiceIds.length === 0 ? "请先选择音色" : ""}
            </p>
          </div>
        )}
      </main>

      {/* Process Confirmation */}
      <ConfirmDialog
        open={processConfirm !== null}
        title="确认开始处理"
        message={processConfirm ?? ""}
        confirmLabel="开始处理"
        cancelLabel="再看看"
        onConfirm={confirmStartProcess}
        onCancel={() => { setProcessConfirm(null); setPendingProcessData(null); }}
      />

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-16 flex justify-around items-center px-4 bg-black z-50 border-t border-white/5">
        <Link href="/" className="flex flex-col items-center justify-center text-neutral-500 p-2 hover:bg-neutral-800 transition-colors">
          <span className="material-symbols-outlined">home</span>
          <span className="text-xs font-medium">首页</span>
        </Link>
        <Link href="/dashboard" prefetch={false} className="flex flex-col items-center justify-center text-primary bg-neutral-900/50 rounded-lg p-2">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: '"FILL" 1' }}>library_music</span>
          <span className="text-xs font-medium">我的作品</span>
        </Link>
        <Link href="/pricing" className="flex flex-col items-center justify-center text-neutral-500 p-2 hover:bg-neutral-800 transition-colors">
          <span className="material-symbols-outlined">account_balance_wallet</span>
          <span className="text-xs font-medium">充值</span>
        </Link>
      </nav>
    </div>
  );
}
