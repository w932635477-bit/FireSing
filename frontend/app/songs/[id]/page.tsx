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
  statusColor,
  type Song,
  type Segment,
  type VoiceModel,
  type Output,
  type ProcessRequest,
} from "@/lib/api";

export default function SongDetailPage() {
  const params = useParams();
  const router = useRouter();
  const songId = params.id as string;

  const [song, setSong] = useState<Song | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [voices, setVoices] = useState<VoiceModel[]>([]);
  const [outputs, setOutputs] = useState<Output[]>([]);
  const [loading, setLoading] = useState(true);

  // Monologue settings
  const [monologueText, setMonologueText] = useState("");
  const [monologuePosition, setMonologuePosition] = useState<"beginning" | "end">("beginning");

  // Upload states
  const [voiceUploading, setVoiceUploading] = useState(false);
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
      console.error("Failed to load:", e);
    } finally {
      setLoading(false);
    }
  }, [songId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleUploadLrc(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const lrc = fd.get("lrc") as File;
    if (!lrc || lrc.size === 0) return;
    setLrcUploading(true);
    try {
      await uploadLrc(songId, lrc);
      await load();
    } catch (e) {
      alert(`LRC 上传失败: ${e instanceof Error ? e.message : e}`);
    } finally {
      setLrcUploading(false);
    }
  }

  async function handleAssignRoundRobin() {
    if (voices.length === 0) return alert("请先上传音色模型");
    try {
      await assignVoices(songId, {
        voice_pool: voices.map((v) => v.id),
        strategy: "round-robin",
      });
      await load();
    } catch (e) {
      alert(`分配失败: ${e instanceof Error ? e.message : e}`);
    }
  }

  async function handleAssignRandom() {
    if (voices.length === 0) return alert("请先上传音色模型");
    try {
      await assignVoices(songId, {
        voice_pool: voices.map((v) => v.id),
        strategy: "random",
      });
      await load();
    } catch (e) {
      alert(`分配失败: ${e instanceof Error ? e.message : e}`);
    }
  }

  async function handleManualAssign(segId: string, voiceId: string) {
    const seg = segments.find((s) => s.id === segId);
    if (!seg) return;
    try {
      await assignVoices(songId, {
        assignments: [{ line_number: seg.line_number, voice_model_id: voiceId }],
        strategy: "manual",
      });
      await load();
    } catch (e) {
      alert(`分配失败: ${e instanceof Error ? e.message : e}`);
    }
  }

  async function handleUploadVoice(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const pth = fd.get("pth_file") as File;
    const idx = fd.get("index_file") as File;
    const name = fd.get("name") as string;
    if (!pth || !name) return;
    setVoiceUploading(true);
    try {
      await uploadVoice(pth, idx?.size > 0 ? idx : null, name);
      await load();
    } catch (e) {
      alert(`音色上传失败: ${e instanceof Error ? e.message : e}`);
    } finally {
      setVoiceUploading(false);
    }
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

    try {
      await startProcess(songId, req);
      router.push(`/songs/${songId}/process`);
    } catch (e) {
      alert(`启动失败: ${e instanceof Error ? e.message : e}`);
    }
  }

  if (loading) return <div className="p-8 text-gray-400">加载中...</div>;
  if (!song) return <div className="p-8 text-red-500">歌曲不存在</div>;

  const hasSegments = segments.length > 0;
  const allAssigned = segments.length > 0 && segments.every((s) => s.voice_model_id);
  const canProcess = allAssigned && !["separating", "segmenting", "assigning", "converting", "chorus", "monologue", "mixing", "video"].includes(song.status);
  const isDone = song.status === "done";

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{song.title}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(song.status)}`}>
              {statusLabel(song.status)}
            </span>
            {song.error_message && (
              <span className="text-xs text-red-500">{song.error_message}</span>
            )}
          </div>
        </div>
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">← 返回列表</Link>
      </div>

      {/* LRC Upload (if no LRC) */}
      {song.status === "uploaded" && !song.lrc_path && (
        <div className="bg-white rounded-xl border p-5">
          <h2 className="font-semibold mb-3">上传歌词文件</h2>
          <form onSubmit={handleUploadLrc} className="flex gap-3 items-end">
            <input name="lrc" type="file" accept=".lrc,.txt" required className="text-sm" />
            <button type="submit" disabled={lrcUploading} className="px-4 py-1.5 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800 disabled:opacity-50">
              {lrcUploading ? "上传中..." : "上传 LRC"}
            </button>
          </form>
        </div>
      )}

      {/* Voice Models */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">音色模型 ({voices.length})</h2>
          <details className="group">
            <summary className="text-sm text-blue-600 cursor-pointer">+ 上传新音色</summary>
            <form onSubmit={handleUploadVoice} className="mt-3 space-y-2 border-t pt-3">
              <input name="name" placeholder="音色名称" required className="w-full px-3 py-1.5 border rounded text-sm" />
              <div className="flex gap-3">
                <input name="pth_file" type="file" accept=".pth" required className="text-sm flex-1" />
                <input name="index_file" type="file" accept=".index" className="text-sm flex-1" />
              </div>
              <button type="submit" disabled={voiceUploading} className="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50">
                {voiceUploading ? "上传中..." : "上传"}
              </button>
            </form>
          </details>
        </div>
        {voices.length === 0 ? (
          <p className="text-sm text-gray-400">还没有音色模型，请上传 .pth 文件</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {voices.map((v) => (
              <span key={v.id} className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm">
                {v.name}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Segment List + Voice Assignment */}
      {hasSegments && (
        <div className="bg-white rounded-xl border p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">歌词段落 ({segments.length})</h2>
            <div className="flex gap-2">
              <button onClick={handleAssignRoundRobin} className="px-3 py-1 bg-blue-50 text-blue-700 rounded text-sm hover:bg-blue-100">
                Round-Robin
              </button>
              <button onClick={handleAssignRandom} className="px-3 py-1 bg-blue-50 text-blue-700 rounded text-sm hover:bg-blue-100">
                随机分配
              </button>
            </div>
          </div>
          <div className="space-y-1">
            {segments.map((seg) => (
              <div key={seg.id} className="flex items-center gap-3 py-2 border-b last:border-0">
                <span className="w-8 text-xs text-gray-400 font-mono">{seg.line_number}</span>
                <span className="flex-1 text-sm text-gray-900">{seg.text}</span>
                <span className="text-xs text-gray-400">
                  {seg.start_time.toFixed(1)}s - {seg.end_time.toFixed(1)}s
                </span>
                <select
                  value={seg.voice_model_id || ""}
                  onChange={(e) => handleManualAssign(seg.id, e.target.value)}
                  className="text-sm border rounded px-2 py-1"
                >
                  <option value="">未分配</option>
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>{v.name}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Process Controls */}
      {canProcess && (
        <div className="bg-white rounded-xl border p-5 space-y-4">
          <h2 className="font-semibold">处理设置</h2>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm text-gray-600 mb-1">独白文本（可选）</label>
              <input
                value={monologueText}
                onChange={(e) => setMonologueText(e.target.value)}
                placeholder="大家好，我是..."
                className="w-full px-3 py-1.5 border rounded text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">位置</label>
              <select
                value={monologuePosition}
                onChange={(e) => setMonologuePosition(e.target.value as "beginning" | "end")}
                className="border rounded px-2 py-1.5 text-sm"
              >
                <option value="beginning">开头</option>
                <option value="end">结尾</option>
              </select>
            </div>
          </div>
          <button
            onClick={handleStartProcess}
            className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
          >
            开始处理
          </button>
        </div>
      )}

      {/* Active processing indicator */}
      {["separating", "segmenting", "assigning", "converting", "chorus", "monologue", "mixing", "video"].includes(song.status) && (
        <div className="bg-blue-50 rounded-xl border border-blue-200 p-5 text-center">
          <p className="text-blue-700 font-medium">正在处理中...</p>
          <Link href={`/songs/${songId}/process`} className="text-sm text-blue-600 underline mt-1 inline-block">
            查看进度
          </Link>
        </div>
      )}

      {/* Outputs */}
      {isDone && outputs.length > 0 && (
        <div className="bg-white rounded-xl border p-5">
          <h2 className="font-semibold mb-4">输出文件</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {outputs.map((out) => (
              <div key={out.id} className="border rounded-lg p-4 flex flex-col items-center gap-3">
                {out.format === "video" ? (
                  <video controls className="w-full rounded" src={out.file_url}>
                    <track kind="captions" />
                  </video>
                ) : (
                  <audio controls className="w-full" src={out.file_url} />
                )}
                <div className="flex items-center gap-2 w-full">
                  <span className="text-sm text-gray-600 flex-1">
                    {out.format === "video" ? "视频 (MP4)" : "音频 (WAV)"}
                    {out.duration && ` · ${out.duration.toFixed(0)}s`}
                    {out.file_size && ` · ${(out.file_size / 1024 / 1024).toFixed(1)}MB`}
                  </span>
                  <a
                    href={out.file_url}
                    download
                    className="px-3 py-1 bg-gray-900 text-white rounded text-sm hover:bg-gray-800"
                  >
                    下载
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
