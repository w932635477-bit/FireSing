const API_BASE = "/api";

// --- Types ---

export interface Song {
  id: string;
  title: string;
  status: string;
  lrc_path?: string | null;
  vocals_path?: string | null;
  instrumental_path?: string | null;
  monologue_text?: string | null;
  monologue_position?: string | null;
  monologue_audio_path?: string | null;
  error_message?: string | null;
  source?: string | null;
  source_id?: string | null;
  artist?: string | null;
  created_at?: string | null;
}

export interface Segment {
  id: string;
  line_number: number;
  text: string;
  start_time: number;
  end_time: number;
  vocal_path?: string | null;
  voice_model_id?: string | null;
  converted_vocal_path?: string | null;
}

export interface VoiceModel {
  id: string;
  name: string;
  is_preset: boolean;
}

export interface Output {
  id: string;
  format: string;
  file_url: string;
  file_size?: number | null;
  duration?: number | null;
}

export interface PipelineProgress {
  step: string;
  pct: number;
  message: string;
  step_failed?: string | null;
  error_detail?: string | null;
}

export interface MusicSearchSong {
  id: string;
  name: string;
  artist: string;
  album: string | null;
  duration: number;
  cover_url: string | null;
  source: string;
  platforms: {
    source: string;
    id: string;
    name: string;
    duration: number;
    cover_url: string;
    source_name: string;
  }[];
  platform_count: number;
}

export interface MusicSearchResponse {
  songs: MusicSearchSong[];
  count: number;
}

export interface MusicImportProgress {
  step: string;
  pct: number;
  message: string;
  song_id?: string;
}

export interface VoiceAssignRequest {
  assignments?: { line_number: number; voice_model_id: string }[];
  voice_pool?: string[];
  strategy: "manual" | "round-robin" | "random";
}

export interface ProcessRequest {
  voice_pool: string[];
  strategy: "round-robin" | "random";
  monologue_text?: string;
  monologue_position?: "beginning" | "end" | "interlude";
  output_format?: "video" | "audio" | "video_subtitled";
  enable_chorus?: boolean;
  chorus_voice_count?: number;
}

// --- Error Types ---

export class AppError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

// --- Helpers ---

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new AppError(0, "network", "无法连接到服务器");
  }
  if (!res.ok) {
    const body = await res.text().catch(() => "Unknown error");
    throw new AppError(res.status, "api", `API ${res.status}: ${body}`);
  }
  return res.json();
}

// --- Songs ---

export async function listSongs(): Promise<{ songs: Song[] }> {
  return apiFetch("/songs");
}

export async function getSong(id: string): Promise<Song> {
  return apiFetch(`/songs/${id}`);
}

export async function uploadSong(audio: File, lrc?: File): Promise<Song> {
  const form = new FormData();
  form.append("audio", audio);
  if (lrc) form.append("lrc", lrc);
  return apiFetch("/songs", { method: "POST", body: form });
}

export async function deleteSong(id: string): Promise<void> {
  await apiFetch(`/songs/${id}`, { method: "DELETE" });
}

export async function uploadLrc(songId: string, lrc: File) {
  const form = new FormData();
  form.append("lrc", lrc);
  return apiFetch(`/songs/${songId}/lrc`, { method: "PUT", body: form });
}

export async function uploadMonologueAudio(songId: string, audio: File) {
  const form = new FormData();
  form.append("audio", audio);
  return apiFetch(`/songs/${songId}/monologue-audio`, { method: "PUT", body: form });
}

export async function updateSegmentTimestamps(
  songId: string,
  segmentId: string,
  data: { start_time?: number; end_time?: number },
) {
  return apiFetch(`/songs/${songId}/segments/${segmentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function getSegments(songId: string): Promise<{ segments: Segment[] }> {
  return apiFetch(`/songs/${songId}/segments`);
}

export async function assignVoices(songId: string, req: VoiceAssignRequest) {
  return apiFetch(`/songs/${songId}/voices`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

// --- Voices ---

export async function listVoices(): Promise<{ voices: VoiceModel[] }> {
  return apiFetch("/voices");
}

export async function uploadVoice(pth: File, index: File | null, name: string): Promise<VoiceModel> {
  const form = new FormData();
  form.append("pth_file", pth);
  if (index) form.append("index_file", index);
  form.append("name", name);
  return apiFetch("/voices", { method: "POST", body: form });
}

// --- Pipeline ---

export async function startProcess(songId: string, req: ProcessRequest) {
  return apiFetch(`/songs/${songId}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export function connectProgress(
  songId: string,
  onProgress: (p: PipelineProgress) => void,
  onError?: (e: Event) => void,
): EventSource {
  const es = new EventSource(`${API_BASE}/songs/${songId}/progress`);
  es.onmessage = (e) => {
    const data: PipelineProgress = JSON.parse(e.data);
    onProgress(data);
    if (data.step === "done" || data.step === "error") {
      es.close();
    }
  };
  es.onerror = (e) => {
    if (onError) onError(e);
  };
  return es;
}

// --- Outputs ---

export async function getOutputs(songId: string): Promise<{ outputs: Output[] }> {
  return apiFetch(`/songs/${songId}/outputs`);
}

// --- Cancel ---

export async function cancelProcess(songId: string): Promise<void> {
  await apiFetch(`/songs/${songId}/process`, { method: "DELETE" });
}

// --- Status helpers ---

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    uploaded: "已上传",
    importing: "导入中",
    separating: "分离人声",
    separated: "已分离",
    segmented: "已切分",
    assigning: "分配音色",
    converting: "RVC 转换",
    chorus: "合唱检测",
    monologue: "生成独白",
    mixing: "混音",
    video: "生成视频",
    done: "完成",
    error: "错误",
  };
  return map[status] || status;
}

export function statusColor(status: string): string {
  if (status === "done") return "bg-green-100 text-green-800";
  if (status === "error") return "bg-red-100 text-red-800";
  if (["uploaded"].includes(status)) return "bg-gray-100 text-gray-800";
  return "bg-blue-100 text-blue-800";
}

// --- Music Search ---

export async function searchMusic(
  q: string,
  sources = ["netease", "qq", "kugou"],
): Promise<MusicSearchResponse> {
  const params = new URLSearchParams({ q });
  sources.forEach((s) => params.append("sources", s));
  return apiFetch(`/music/search?${params}`);
}

export async function checkMusicExisting(
  source: string,
  sourceId: string,
): Promise<{ exists: boolean; song_id: string | null }> {
  const params = new URLSearchParams({ source, source_id: sourceId });
  return apiFetch(`/music/check-existing?${params}`);
}

export async function importMusic(
  source: string,
  sourceId: string,
  title: string,
  artist = "",
): Promise<{ task_id: string; status: string }> {
  const params = new URLSearchParams({
    source,
    source_id: sourceId,
    title,
    artist,
  });
  return apiFetch(`/music/import?${params}`, { method: "POST" });
}

// --- Auth ---

export interface UserInfo {
  authenticated: boolean;
  id?: string;
  nickname?: string;
  avatar_url?: string;
  credits?: number;
  plan?: string;
  has_unlimited?: boolean;
}

export interface OrderInfo {
  id: string;
  type: string;
  amount: number;
  credits_amount?: number | null;
  description: string;
  status: string;
  paid_at?: string | null;
  created_at?: string | null;
}

export interface PricingPlan {
  id: string;
  credits?: number;
  price_fen: number;
  name: string;
  desc: string;
}

const TOKEN_KEY = "firesing_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string> || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return apiFetch(path, { ...init, headers });
}

export async function getMe(): Promise<UserInfo> {
  return authFetch("/auth/me");
}

export async function getQrLoginUrl(): Promise<{ url: string; state: string }> {
  return apiFetch("/auth/wechat/qr-url");
}

export async function pollLogin(state: string): Promise<{ status: string; token?: string }> {
  return apiFetch(`/auth/wechat/poll?state=${state}`);
}

export async function getPlans(): Promise<{ credits: PricingPlan[]; subscriptions: PricingPlan[] }> {
  return apiFetch("/orders/plans");
}

export async function createOrder(
  planId: string,
): Promise<{ order_id: string; status: string; amount: number; qr_url?: string }> {
  return authFetch(`/orders/create?plan_id=${planId}`, { method: "POST" });
}

export async function getOrder(orderId: string): Promise<OrderInfo> {
  return authFetch(`/orders/${orderId}`);
}

export async function listOrders(): Promise<{ orders: OrderInfo[] }> {
  return authFetch("/orders");
}

export function connectImportProgress(
  taskId: string,
  onProgress: (p: MusicImportProgress) => void,
  onDone?: (songId: string) => void,
  onError?: (msg: string) => void,
): EventSource {
  const es = new EventSource(`${API_BASE}/music/import/${taskId}/progress`);
  es.onmessage = (e) => {
    const data: MusicImportProgress = JSON.parse(e.data);
    onProgress(data);
    if (data.step === "done") {
      es.close();
      if (onDone && data.song_id) onDone(data.song_id);
    }
    if (data.step === "error") {
      es.close();
      if (onError) onError(data.message);
    }
  };
  es.onerror = () => {
    if (onError) onError("连接中断");
    es.close();
  };
  return es;
}
