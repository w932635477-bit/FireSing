"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  getSong,
  getSegments,
  assignVoices,
  listVoices,
  uploadVoice,
  uploadLrc,
  getOutputs,
  startProcess,
  uploadMonologueAudio,
  type Song,
  type Segment,
  type VoiceModel,
  type Output,
  type ProcessRequest,
} from "@/lib/api";
import { useToast } from "@/components/Toast";

export const VOICE_COLORS = [
  { chip: "voice-chip-red", dot: "bg-ember", label: "珊瑚红" },
  { chip: "voice-chip-green", dot: "bg-success", label: "薄荷绿" },
  { chip: "voice-chip-blue", dot: "bg-secondary", label: "天蓝色" },
  { chip: "voice-chip-gray", dot: "bg-on-surface-variant", label: "灰绿色" },
  { chip: "voice-chip-purple", dot: "bg-purple-400", label: "紫罗兰" },
  { chip: "voice-chip-orange", dot: "bg-orange-400", label: "橘黄色" },
  { chip: "voice-chip-pink", dot: "bg-pink-400", label: "粉红色" },
  { chip: "voice-chip-teal", dot: "bg-teal-400", label: "青碧色" },
];

export type Tab = "detail" | "library" | "studio";

export function useSongDetail(songId: string) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { addToast } = useToast();

  const [song, setSong] = useState<Song | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [voices, setVoices] = useState<VoiceModel[]>([]);
  const [outputs, setOutputs] = useState<Output[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("detail");

  const [monologueText, setMonologueText] = useState("");
  const [monologueMode, setMonologueMode] = useState<"text" | "record">("text");
  const [monologuePosition, setMonologuePosition] = useState<"beginning" | "end">("beginning");
  const [monologueFile, setMonologueFile] = useState<File | null>(null);
  const [monologueUploading, setMonologueUploading] = useState(false);
  const [outputFormat, setOutputFormat] = useState<"video" | "audio" | "video_subtitled">("video");
  const [enableChorus, setEnableChorus] = useState(true);
  const [chorusVoiceCount, setChorusVoiceCount] = useState(5);
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
    } catch {
      // API unavailable — use demo data for UI preview
      console.warn("API unavailable, showing demo data for song detail");
      setSong({
        id: songId,
        title: "稻香",
        status: "segmented",
        lrc_path: "/data/demo.lrc",
        source: "netease",
        artist: "周杰伦",
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

  // Auto-switch tab from URL query param (e.g. ?tab=studio from process page retry)
  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab === "library" || tab === "studio" || tab === "detail") {
      setActiveTab(tab);
    }
  }, [searchParams]);

  async function handleUploadLrc(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const lrc = fd.get("lrc") as File;
    if (!lrc || lrc.size === 0) { addToast("warning", "请选择 LRC 歌词文件"); return; }
    setLrcUploading(true);
    try { await uploadLrc(songId, lrc); await load(); }
    catch (e) { addToast("error", `LRC 上传失败，请检查文件格式是否为 .lrc 或 .txt。错误: ${e instanceof Error ? e.message : "请重试"}`); }
    finally { setLrcUploading(false); }
  }

  async function handleAssign(strategy: "manual" | "round-robin" | "random", options?: { segId?: string; voiceId?: string }) {
    if (strategy !== "manual" && voices.length === 0) {
      addToast("warning", "请先上传音色模型");
      return;
    }
    try {
      if (strategy === "manual" && options?.segId && options?.voiceId) {
        const seg = segments.find((s) => s.id === options.segId);
        if (!seg) return;
        await assignVoices(songId, { assignments: [{ line_number: seg.line_number, voice_model_id: options.voiceId }], strategy: "manual" });
      } else {
        await assignVoices(songId, { voice_pool: voices.map((v) => v.id), strategy });
      }
      await load();
    } catch (e) {
      addToast("error", `音色分配失败，请检查音色模型是否有效。错误: ${e instanceof Error ? e.message : "请重试"}`);
    }
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
    catch (e) { addToast("error", `音色上传失败，请确保 .pth 文件格式正确。错误: ${e instanceof Error ? e.message : "请重试"}`); }
    finally { setVoiceUploading(false); }
  }

  async function handleStartProcess() {
    const assigned = segments.filter((s) => s.voice_model_id);
    if (assigned.length === 0) { addToast("warning", "请先分配音色"); return; }
    const pool = [...new Set(assigned.map((s) => s.voice_model_id!))];

    // Confirm before starting
    const voiceNames = pool.map(id => voices.find(v => v.id === id)?.name || id).join(", ");
    const fmt = outputFormat === "video" ? "竖版视频" : outputFormat === "audio" ? "纯音频" : "字幕视频";
    const summary = `即将开始处理:\n音色: ${voiceNames}\n输出格式: ${fmt}${enableChorus ? `\n合唱: ${chorusVoiceCount}声部` : ""}${monologueText ? `\n独白: ${monologueText.slice(0, 30)}...` : ""}`;
    if (!confirm(summary)) return;

    // Upload monologue recording if selected
    if (monologueMode === "record" && monologueFile) {
      setMonologueUploading(true);
      try { await uploadMonologueAudio(songId, monologueFile); }
      catch (e) { setMonologueUploading(false); return addToast("error", `独白上传失败: ${e instanceof Error ? e.message : "请重试"}`); }
      finally { setMonologueUploading(false); }
    }

    const req: ProcessRequest = {
      voice_pool: pool,
      strategy: "round-robin",
      monologue_text: monologueMode === "text" && monologueText ? monologueText : undefined,
      monologue_position: monologuePosition,
      output_format: outputFormat,
      enable_chorus: enableChorus,
      chorus_voice_count: chorusVoiceCount,
    };
    try { await startProcess(songId, req); router.push(`/songs/${songId}/process`); }
    catch (e) { addToast("error", `处理启动失败，请检查所有设置后重试。错误: ${e instanceof Error ? e.message : "请重试"}`); }
  }

  // Computed values
  const hasSegments = segments.length > 0;
  const allAssigned = segments.length > 0 && segments.every((s) => s.voice_model_id);
  const canProcess = allAssigned && !["separating", "segmenting", "assigning", "converting", "chorus", "monologue", "mixing", "video"].includes(song?.status ?? "");
  const isProcessing = song ? ["separating", "segmenting", "assigning", "converting", "chorus", "monologue", "mixing", "video"].includes(song.status) : false;
  const isDone = song?.status === "done";

  return {
    // State
    song,
    segments,
    setSegments,
    voices,
    outputs,
    loading,
    activeTab,
    setActiveTab,
    monologueText,
    setMonologueText,
    monologueMode,
    setMonologueMode,
    monologuePosition,
    setMonologuePosition,
    monologueFile,
    setMonologueFile,
    monologueUploading,
    outputFormat,
    setOutputFormat,
    enableChorus,
    setEnableChorus,
    chorusVoiceCount,
    setChorusVoiceCount,
    voiceUploading,
    lrcUploading,
    showVoiceUpload,
    setShowVoiceUpload,
    // Handlers
    handleUploadLrc,
    handleAssign,
    handleUploadVoice,
    handleStartProcess,
    // Computed
    hasSegments,
    allAssigned,
    canProcess,
    isProcessing,
    isDone,
  };
}
