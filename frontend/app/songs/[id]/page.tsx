"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getSong,
  getSegments,
  assignVoices,
  listVoices,
  uploadVoice,
  uploadLrc,
  getOutputs,
  startProcess,
  statusLabel,
  type Song,
  type Segment,
  type VoiceModel,
  type Output,
  type ProcessRequest,
} from "@/lib/api";

const VOICE_COLORS = [
  { chip: "voice-chip-red", dot: "bg-ember", label: "珊瑚红" },
  { chip: "voice-chip-green", dot: "bg-success", label: "薄荷绿" },
  { chip: "voice-chip-blue", dot: "bg-secondary", label: "天蓝色" },
  { chip: "voice-chip-gray", dot: "bg-on-surface-variant", label: "灰绿色" },
  { chip: "voice-chip-red", dot: "bg-ember", label: "珊瑚红" },
  { chip: "voice-chip-green", dot: "bg-success", label: "薄荷绿" },
  { chip: "voice-chip-blue", dot: "bg-secondary", label: "天蓝色" },
  { chip: "voice-chip-gray", dot: "bg-on-surface-variant", label: "灰绿色" },
];

type Tab = "detail" | "library" | "studio";

export default function SongDetailPage() {
  const params = useParams();
  const router = useRouter();
  const songId = params.id as string;

  const [song, setSong] = useState<Song | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [voices, setVoices] = useState<VoiceModel[]>([]);
  const [outputs, setOutputs] = useState<Output[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("detail");

  const [monologueText, setMonologueText] = useState("");
  const [monologuePosition, setMonologuePosition] = useState<"beginning" | "end">("beginning");
  const [voiceUploading, setVoiceUploading] = useState(false);
  const [lrcUploading, setLrcUploading] = useState(false);
  const [showVoiceUpload, setShowVoiceUpload] = useState(false);

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
      // API unavailable — use demo data for UI preview
      console.warn("API unavailable, showing demo data for song detail");
      setSong({
        id: songId,
        title: "稻香",
        status: "segmented",
        lrc_path: "/data/demo.lrc",
        created_at: "2025-04-04T16:00:00Z",
      });
      setVoices([
        { id: "voice-1", name: "周杰伦音色", is_preset: false },
        { id: "voice-2", name: "林俊杰音色", is_preset: false },
        { id: "voice-3", name: "邓紫棋音色", is_preset: true },
      ]);
      setSegments([
        { id: "seg-1", line_number: 1, text: "对这个世界如果你有太多的抱怨", start_time: 12.5, end_time: 16.8, voice_model_id: "voice-1" },
        { id: "seg-2", line_number: 2, text: "跌倒了就不敢继续往前走", start_time: 17.0, end_time: 20.3, voice_model_id: "voice-2" },
        { id: "seg-3", line_number: 3, text: "为什么人要这么的脆弱 堕落", start_time: 20.5, end_time: 24.1, voice_model_id: "voice-3" },
        { id: "seg-4", line_number: 4, text: "请你打开电视看看", start_time: 24.3, end_time: 27.0 },
        { id: "seg-5", line_number: 5, text: "多少人为生命在努力勇敢的走下去", start_time: 27.2, end_time: 31.5, voice_model_id: "voice-1" },
        { id: "seg-6", line_number: 6, text: "我们是不是该知足", start_time: 31.7, end_time: 34.2 },
        { id: "seg-7", line_number: 7, text: "珍惜一切 就算没有拥有", start_time: 34.4, end_time: 38.0, voice_model_id: "voice-2" },
      ]);
    } finally {
      setLoading(false);
    }
  }, [songId]);

  useEffect(() => { load(); }, [load]);

  async function handleUploadLrc(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const lrc = fd.get("lrc") as File;
    if (!lrc || lrc.size === 0) return;
    setLrcUploading(true);
    try { await uploadLrc(songId, lrc); await load(); }
    catch (e) { alert(`LRC 上传失败: ${e instanceof Error ? e.message : e}`); }
    finally { setLrcUploading(false); }
  }

  async function handleAssignRoundRobin() {
    if (voices.length === 0) return alert("请先上传音色模型");
    try { await assignVoices(songId, { voice_pool: voices.map((v) => v.id), strategy: "round-robin" }); await load(); }
    catch (e) { alert(`分配失败: ${e instanceof Error ? e.message : e}`); }
  }

  async function handleManualAssign(segId: string, voiceId: string) {
    const seg = segments.find((s) => s.id === segId);
    if (!seg) return;
    try { await assignVoices(songId, { assignments: [{ line_number: seg.line_number, voice_model_id: voiceId }], strategy: "manual" }); await load(); }
    catch (e) { alert(`分配失败: ${e instanceof Error ? e.message : e}`); }
  }

  async function handleUploadVoice(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const pth = fd.get("pth_file") as File;
    const idx = fd.get("index_file") as File;
    const name = fd.get("name") as string;
    if (!pth || !name) return;
    setVoiceUploading(true);
    try { await uploadVoice(pth, idx?.size > 0 ? idx : null, name); await load(); setShowVoiceUpload(false); }
    catch (e) { alert(`音色上传失败: ${e instanceof Error ? e.message : e}`); }
    finally { setVoiceUploading(false); }
  }

  async function handleStartProcess() {
    const assigned = segments.filter((s) => s.voice_model_id);
    if (assigned.length === 0) return alert("请先分配音色");
    const pool = [...new Set(assigned.map((s) => s.voice_model_id!))];
    const req: ProcessRequest = {
      voice_pool: pool,
      strategy: "round-robin",
      monologue_text: monologueText || undefined,
      monologue_position: monologuePosition,
    };
    try { await startProcess(songId, req); router.push(`/songs/${songId}/process`); }
    catch (e) { alert(`启动失败: ${e instanceof Error ? e.message : e}`); }
  }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <span className="material-symbols-outlined text-5xl text-ember animate-pulse">hourglass_empty</span>
    </div>
  );
  if (!song) return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-error text-lg">歌曲不存在</p>
    </div>
  );

  const hasSegments = segments.length > 0;
  const allAssigned = segments.length > 0 && segments.every((s) => s.voice_model_id);
  const canProcess = allAssigned && !["separating", "segmenting", "assigning", "converting", "chorus", "monologue", "mixing", "video"].includes(song.status);
  const isProcessing = ["separating", "segmenting", "assigning", "converting", "chorus", "monologue", "mixing", "video"].includes(song.status);
  const isDone = song.status === "done";

  return (
    <div className="bg-surface-container-lowest min-h-screen">
      {/* Top Nav */}
      <header className="fixed top-0 w-full flex justify-between items-center px-6 py-4 bg-black/60 backdrop-blur-xl z-50 shadow-[0_8px_32px_rgba(255,107,53,0.15)]">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-2xl font-black text-ember tracking-tight">FireSing</Link>
          <div className="h-6 w-px bg-white/10 mx-2" />
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-white tracking-tight">{song.title}</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-ember/20 text-ember border border-ember/30 flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-full ${isDone ? "bg-success" : isProcessing ? "bg-warning animate-pulse" : song.status === "error" ? "bg-error" : "bg-ember"} ${isProcessing ? "animate-pulse" : ""}`} />
              {statusLabel(song.status)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <nav className="hidden md:flex items-center gap-6">
            <button onClick={() => setActiveTab("detail")} className={`py-1 text-sm transition-colors ${activeTab === "detail" ? "text-ember font-bold border-b-2 border-ember" : "text-white/60 font-medium hover:text-white"}`}>详情</button>
            <button onClick={() => setActiveTab("library")} className={`py-1 text-sm transition-colors ${activeTab === "library" ? "text-ember font-bold border-b-2 border-ember" : "text-white/60 font-medium hover:text-white"}`}>曲库</button>
            <button onClick={() => setActiveTab("studio")} className={`py-1 text-sm transition-colors ${activeTab === "studio" ? "text-ember font-bold border-b-2 border-ember" : "text-white/60 font-medium hover:text-white"}`}>工作室</button>
          </nav>
          <Link href="/dashboard" className="bg-ember text-on-primary-fixed font-bold px-4 py-2 rounded-lg text-sm hover:scale-[0.98] transition-transform active:brightness-90">
            上传新歌曲
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto pt-28 pb-20 px-6">
        {/* Tab: Detail — shows LRC upload + LRC status + voice models */}
        {(activeTab === "detail") && song.status === "uploaded" && !song.lrc_path && (
          <section className="mb-10">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">description</span>
              1. 歌词文件
            </h2>
            <div className="bg-surface-container-low rounded-xl p-5 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-surface-container-high flex items-center justify-center text-ember">
                  <span className="material-symbols-outlined text-3xl">lyrics</span>
                </div>
                <div>
                  <div className="font-bold text-white">上传 LRC 歌词文件</div>
                  <div className="text-sm text-on-surface-variant">支持 .lrc 和 .txt 格式</div>
                </div>
              </div>
              <form onSubmit={handleUploadLrc} className="flex gap-3 items-center">
                <input name="lrc" type="file" accept=".lrc,.txt" required className="text-sm text-on-surface-variant file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-ember/20 file:text-ember" />
                <button type="submit" disabled={lrcUploading} className="px-4 py-2 bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed rounded-lg text-sm font-bold disabled:opacity-50 active:scale-[0.98] transition-transform">
                  {lrcUploading ? "上传中..." : "上传"}
                </button>
              </form>
            </div>
          </section>
        )}

        {/* LRC uploaded confirmation */}
        {(activeTab === "detail") && song.lrc_path && (
          <section className="mb-10">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">description</span>
              1. 歌词文件
            </h2>
            <div className="bg-surface-container-low rounded-xl p-5 flex items-center justify-between group hover:bg-surface-container transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-surface-container-high flex items-center justify-center text-ember">
                  <span className="material-symbols-outlined text-3xl">lyrics</span>
                </div>
                <div>
                  <div className="font-bold text-white">歌词已上传</div>
                  <div className="text-sm text-on-surface-variant font-mono">LRC 文件就绪</div>
                </div>
              </div>
              <div className="flex items-center gap-2 text-success font-bold text-sm bg-success/10 px-3 py-1.5 rounded-full">
                <span>已就绪</span>
                <span className="material-symbols-outlined text-sm">check_circle</span>
              </div>
            </div>
          </section>
        )}

        {/* 2. Voice Models — visible on detail tab */}
        {(activeTab === "detail") && (
        <section className="mb-10">
          <div className="flex justify-between items-end mb-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">record_voice_over</span>
              2. 音色模型
            </h2>
            <button
              onClick={() => setShowVoiceUpload(!showVoiceUpload)}
              className="text-xs font-bold text-ember hover:underline flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-xs">add</span>
              上传新音色
            </button>
          </div>

          {showVoiceUpload && (
            <form onSubmit={handleUploadVoice} className="bg-surface-container-low rounded-xl p-5 mb-4 space-y-3 border border-ember/20">
              <input name="name" placeholder="音色名称" required className="w-full bg-surface-container-high text-on-surface px-4 py-2.5 rounded-lg text-sm focus:ring-2 focus:ring-ember/40 transition-all placeholder:text-on-surface-variant/40" />
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-[10px] text-on-surface-variant uppercase tracking-wider mb-1">.pth 模型文件 *</label>
                  <input name="pth_file" type="file" accept=".pth" required className="w-full text-sm text-on-surface-variant file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-ember/20 file:text-ember" />
                </div>
                <div className="flex-1">
                  <label className="block text-[10px] text-on-surface-variant uppercase tracking-wider mb-1">.index 索引文件</label>
                  <input name="index_file" type="file" accept=".index" className="w-full text-sm text-on-surface-variant file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-surface-container-high file:text-on-surface" />
                </div>
              </div>
              <button type="submit" disabled={voiceUploading} className="px-4 py-2 bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed rounded-lg text-sm font-bold disabled:opacity-50 active:scale-[0.98] transition-transform">
                {voiceUploading ? "上传中..." : "上传音色"}
              </button>
            </form>
          )}

          {voices.length === 0 ? (
            <div className="bg-surface-container-low rounded-xl p-8 text-center">
              <span className="material-symbols-outlined text-4xl text-on-surface-variant/30 mb-3 block">settings_voice</span>
              <p className="text-on-surface-variant text-sm">还没有音色模型，请上传 .pth 文件</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {voices.map((v, i) => {
                const color = VOICE_COLORS[i % VOICE_COLORS.length];
                return (
                  <div key={v.id} className="bg-surface-container-low p-4 rounded-xl border border-white/5 flex flex-col items-center gap-3 hover:bg-surface-container-high transition-all cursor-pointer">
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center bg-surface-container-high border-2 ${color.dot.replace("bg-", "border-")}`}>
                      <span className="material-symbols-outlined text-2xl text-on-surface-variant">mic</span>
                    </div>
                    <div className="text-center">
                      <div className="font-bold text-sm">{v.name}</div>
                      <div className={`text-[10px] font-mono mt-1 px-2 py-0.5 rounded-full ${color.chip}`}>{color.label}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
        )}
        {(activeTab === "library") && hasSegments && (
          <>
          <section className="mb-10">
            <div className="flex justify-between items-end mb-4">
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">segment</span>
                3. 歌词段落
              </h2>
              <div className="flex gap-2">
                <button onClick={handleAssignRoundRobin} className="text-xs font-bold text-ember hover:underline flex items-center gap-1">
                  <span className="material-symbols-outlined text-xs">autorenew</span>
                  轮流分配
                </button>
              </div>
            </div>
            <div className="bg-surface-container-low rounded-xl overflow-hidden border border-white/5">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-high text-[10px] font-bold uppercase text-on-surface-variant tracking-wider">
                    <th className="px-6 py-4">行号</th>
                    <th className="px-6 py-4">歌词文本</th>
                    <th className="px-6 py-4">时间范围</th>
                    <th className="px-6 py-4">音色</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {segments.map((seg, i) => {
                    const color = VOICE_COLORS[voices.findIndex((v) => v.id === seg.voice_model_id) % VOICE_COLORS.length];
                    return (
                      <tr key={seg.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="px-6 py-4 text-xs font-mono text-on-surface-variant">
                          {String(seg.line_number).padStart(2, "0")}
                        </td>
                        <td className="px-6 py-4 text-sm font-medium">{seg.text}</td>
                        <td className="px-6 py-4 text-xs font-mono text-ember">
                          {seg.start_time.toFixed(1)}-{seg.end_time.toFixed(1)}s
                        </td>
                        <td className="px-6 py-4">
                          <select
                            value={seg.voice_model_id || ""}
                            onChange={(e) => handleManualAssign(seg.id, e.target.value)}
                            className={`text-xs font-bold px-3 py-1.5 rounded-lg border-0 appearance-none cursor-pointer ${seg.voice_model_id ? color.chip : "bg-surface-container-high text-on-surface-variant"}`}
                          >
                            <option value="">未分配</option>
                            {voices.map((v) => (
                              <option key={v.id} value={v.id}>{v.name}</option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
        )}

        {/* Tab: Studio — shows processing settings + outputs */}
        {(activeTab === "studio") && canProcess && (
          <section className="mb-12">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">settings_input_component</span>
              4. 处理设置
            </h2>
            <div className="bg-surface-container-low rounded-xl p-6 space-y-6">
              <div>
                <label className="block text-xs font-bold text-white mb-2 uppercase tracking-wide opacity-60">旁白文本</label>
                <textarea
                  value={monologueText}
                  onChange={(e) => setMonologueText(e.target.value)}
                  className="w-full bg-surface-container border-0 focus:ring-1 focus:ring-ember/40 rounded-lg p-4 text-sm font-medium text-white placeholder-white/20 h-24 resize-none"
                  placeholder="输入旁白内容..."
                />
              </div>
              <div className="flex items-center gap-8">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="radio"
                    name="monologue"
                    checked={monologuePosition === "beginning"}
                    onChange={() => setMonologuePosition("beginning")}
                    className="w-4 h-4 accent-ember"
                  />
                  <span className="text-sm font-bold text-white group-hover:text-ember transition-colors">片头 (Intro)</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="radio"
                    name="monologue"
                    checked={monologuePosition === "end"}
                    onChange={() => setMonologuePosition("end")}
                    className="w-4 h-4 accent-ember"
                  />
                  <span className="text-sm font-bold text-white group-hover:text-ember transition-colors">片尾 (Outro)</span>
                </label>
              </div>
            </div>
          </section>
        )}

        {/* Processing indicator — always visible regardless of tab */}
        {isProcessing && (activeTab === "studio" || activeTab === "detail") && (
          <div className="bg-surface-container-low rounded-xl p-5 text-center border border-warning/20 mb-10">
            <span className="material-symbols-outlined text-4xl text-warning animate-pulse mb-2 block">progress_activity</span>
            <p className="text-on-surface font-bold">正在处理中...</p>
            <Link href={`/songs/${songId}/process`} className="text-sm text-ember underline mt-1 inline-block">
              查看进度 →
            </Link>
          </div>
        )}

        {/* Start Process Button — studio tab or detail tab */}
        {(activeTab === "studio" || activeTab === "detail") && canProcess && (
          <div className="flex justify-center pt-6 border-t border-white/5">
            <button
              onClick={handleStartProcess}
              className="w-full md:w-auto min-w-[280px] bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed font-black text-lg px-8 py-5 rounded-xl flex items-center justify-center gap-3 shadow-[0_8px_32px_rgba(255,107,53,0.3)] hover:scale-[0.98] active:scale-[0.96] transition-all"
            >
              <span className="material-symbols-outlined font-bold" style={{ fontVariationSettings: '"FILL" 1' }}>play_arrow</span>
              开始处理
            </button>
          </div>
        )}

        {/* Outputs — visible on studio tab */}
        {(activeTab === "studio") && isDone && outputs.length > 0 && (
          <section className="mt-10">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">download</span>
              输出文件
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {outputs.map((out) => (
                <div key={out.id} className="bg-surface-container-low rounded-xl p-5 border border-white/5">
                  {out.format === "video" ? (
                    <video controls className="w-full rounded-lg mb-4" src={out.file_url}>
                      <track kind="captions" />
                    </video>
                  ) : (
                    <audio controls className="w-full mb-4" src={out.file_url} />
                  )}
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-on-surface-variant font-mono">
                      {out.format === "video" ? "视频 (MP4)" : "音频 (WAV)"}
                      {out.duration && ` · ${out.duration.toFixed(0)}s`}
                      {out.file_size && ` · ${(out.file_size / 1024 / 1024).toFixed(1)}MB`}
                    </div>
                    <a
                      href={out.file_url}
                      download
                      className="px-4 py-2 bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed rounded-lg text-sm font-bold active:scale-[0.98] transition-transform flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-sm">download</span>
                      下载
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Side decoration */}
      <div className="fixed bottom-8 left-8 hidden lg:block">
        <div className="text-[10px] font-mono text-white/20 rotate-90 origin-left uppercase tracking-[0.4em] whitespace-nowrap">
          黑曜石工作室 // 详情页
        </div>
      </div>
    </div>
  );
}
