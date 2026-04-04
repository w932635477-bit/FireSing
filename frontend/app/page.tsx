"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  listSongs,
  uploadSong,
  statusLabel,
  statusColor,
  type Song,
} from "@/lib/api";

export default function Home() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const load = useCallback(async () => {
    try {
      const data = await listSongs();
      setSongs(data.songs || []);
    } catch (e) {
      console.error("Failed to load songs:", e);
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
    const audio = (fd.get("audio") as File) || null;
    const lrc = (fd.get("lrc") as File) || null;

    if (!audio || audio.size === 0) return;

    setUploading(true);
    try {
      const song = await uploadSong(audio, lrc.size > 0 ? lrc : undefined);
      window.location.href = `/songs/${song.id}`;
    } catch (e) {
      alert(`上传失败: ${e instanceof Error ? e.message : e}`);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">我的歌曲</h1>
          <p className="text-gray-500 text-sm mt-1">上传歌曲，AI 替换人声</p>
        </div>
        <button
          onClick={() => dialogRef.current?.showModal()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          + 上传新歌
        </button>
      </div>

      {loading ? (
        <p className="text-gray-400">加载中...</p>
      ) : songs.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-lg mb-2">还没有歌曲</p>
          <p className="text-sm">点击右上角 "上传新歌" 开始</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {songs.map((song) => (
            <Link
              key={song.id}
              href={`/songs/${song.id}`}
              className="block bg-white rounded-xl border p-5 hover:shadow-md transition"
            >
              <h3 className="font-semibold text-gray-900 truncate">
                {song.title}
              </h3>
              <div className="flex items-center gap-2 mt-2">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(song.status)}`}
                >
                  {statusLabel(song.status)}
                </span>
                {song.created_at && (
                  <span className="text-xs text-gray-400">
                    {new Date(song.created_at).toLocaleDateString("zh-CN")}
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Upload Dialog */}
      <dialog ref={dialogRef} className="rounded-xl p-0 backdrop:bg-black/30">
        <div className="p-6 w-[420px]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">上传新歌</h2>
            <button
              onClick={() => dialogRef.current?.close()}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                音频文件 *
              </label>
              <input
                name="audio"
                type="file"
                accept=".mp3,.wav,.flac"
                required
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              <p className="text-xs text-gray-400 mt-1">支持 MP3/WAV/FLAC，最大 50MB</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                LRC 歌词文件（可选）
              </label>
              <input
                name="lrc"
                type="file"
                accept=".lrc,.txt"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100"
              />
            </div>
            <button
              type="submit"
              disabled={uploading}
              className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {uploading ? "上传中..." : "上传"}
            </button>
          </form>
        </div>
      </dialog>
    </div>
  );
}
