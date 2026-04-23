/** Rotas da API FastAPI via proxy server-side (/api/proxy/*). Sem chave no bundle. */
const PROXY_BASE = "/api/proxy"

function toProxyPath(backendPath: string): string {
  const p = backendPath.startsWith("/") ? backendPath.slice(1) : backendPath
  return `${PROXY_BASE}/${p}`
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: string,
  ) {
    super(message)
    this.name = "ApiRequestError"
  }
}

export async function apiFetch(backendPath: string, options: RequestInit = {}): Promise<Response> {
  const url = toProxyPath(backendPath)
  const headers = new Headers(options.headers)
  if (
    !(options.body instanceof FormData) &&
    options.body != null &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json")
  }
  return fetch(url, {
    ...options,
    headers,
    credentials: "include",
  })
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text()
  if (!res.ok) {
    throw new ApiRequestError(text || res.statusText, res.status, text)
  }
  return text ? (JSON.parse(text) as T) : ({} as T)
}

/** KPIs — `period` reservado para evolucao futura da API */
export async function fetchKPIs(_period: "today" | "7d" | "30d"): Promise<KPIResponse> {
  const res = await apiFetch("/analytics/kpis")
  return parseJson<KPIResponse>(res)
}

export async function fetchVolume(granularity: "hour" | "day"): Promise<VolumePoint[]> {
  const res = await apiFetch(`/analytics/volume?granularity=${encodeURIComponent(granularity)}`)
  return parseJson<VolumePoint[]>(res)
}

export async function fetchCategories(): Promise<CategoryPoint[]> {
  const res = await apiFetch("/analytics/categories")
  return parseJson<CategoryPoint[]>(res)
}

export async function fetchTopQuestions(limit: number): Promise<QuestionCount[]> {
  const res = await apiFetch(`/analytics/top-questions?limit=${limit}`)
  return parseJson<QuestionCount[]>(res)
}

export async function fetchConversations(
  page: number,
  size: number,
  period?: "today" | "7d" | "30d",
): Promise<ConversationPage> {
  const q = new URLSearchParams({ page: String(page), size: String(size) })
  if (period) q.set("period", period)
  const res = await apiFetch(`/chat/conversations?${q}`)
  return parseJson<ConversationPage>(res)
}

export async function fetchMessages(conversationId: string): Promise<MessageResponse[]> {
  const res = await apiFetch(`/chat/conversations/${encodeURIComponent(conversationId)}/messages`)
  return parseJson<MessageResponse[]>(res)
}

export async function fetchUnreadCount(): Promise<number> {
  const res = await apiFetch("/conversations/unread-count")
  const data = await parseJson<{ count: number }>(res)
  return data.count
}

export async function fetchDocuments(page: number, size: number): Promise<DocumentPage> {
  const q = new URLSearchParams({ page: String(page), size: String(size) })
  const res = await apiFetch(`/knowledge/documents?${q}`)
  return parseJson<DocumentPage>(res)
}

export async function uploadDocument(
  file: File,
  title: string,
  type: "PROCEDURE" | "FAQ" | "PROTOCOL" | "GENERAL",
): Promise<DocumentResponse> {
  const content_hash = await sha256Hex(file)
  const fd = new FormData()
  fd.append("title", title)
  fd.append("type", type)
  fd.append("content_hash", content_hash)
  fd.append("file", file)
  const res = await apiFetch("/knowledge/documents", { method: "POST", body: fd })
  return parseJson<DocumentResponse>(res)
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await apiFetch(`/knowledge/documents/${encodeURIComponent(id)}`, { method: "DELETE" })
  if (!res.ok) {
    const t = await res.text()
    throw new ApiRequestError(t || res.statusText, res.status, t)
  }
}

export async function searchKnowledge(
  query: string,
  topK: number,
  threshold: number,
): Promise<SearchResult[]> {
  const res = await apiFetch("/knowledge/search", {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK, threshold }),
  })
  return parseJson<SearchResult[]>(res)
}

export async function reindexDocument(id: string): Promise<ReindexQueuedResponse> {
  const res = await apiFetch(`/knowledge/documents/${encodeURIComponent(id)}/reindex`, {
    method: "POST",
  })
  return parseJson<ReindexQueuedResponse>(res)
}

export interface WhatsAppConnectionStatus {
  connected: boolean
  phone_number_id: string
  verified_name?: string | null
  display_phone_number?: string | null
  quality_rating?: string | null
  messaging_limit_tier?: string | null
  error?: string | null
  public_webhook_url?: string | null
  verify_token_configured: boolean
  access_token_configured: boolean
}

export async function fetchSettings(category: string): Promise<SettingResponse[]> {
  const res = await apiFetch(`/settings/${encodeURIComponent(category)}`)
  if (res.status === 404) return []
  return parseJson<SettingResponse[]>(res)
}

export async function fetchWhatsAppConnection(): Promise<WhatsAppConnectionStatus> {
  const res = await apiFetch("/whatsapp/admin/connection")
  return parseJson<WhatsAppConnectionStatus>(res)
}

export async function putWhatsAppCredentials(body: {
  phone_number_id?: string
  access_token?: string
  verify_token?: string
}): Promise<{ status: string }> {
  const res = await apiFetch("/whatsapp/admin/credentials", {
    method: "PUT",
    body: JSON.stringify(body),
  })
  return parseJson<{ status: string }>(res)
}

export async function updateSetting(key: string, value: unknown): Promise<SettingResponse> {
  const res = await apiFetch(`/settings/${encodeURIComponent(key)}`, {
    method: "PUT",
    body: JSON.stringify({ value }),
  })
  return parseJson<SettingResponse>(res)
}

export async function sendTestMessage(message: string, conversationId?: string | null): Promise<ChatResponse> {
  const res = await apiFetch("/chat/message", {
    method: "POST",
    body: JSON.stringify({ message, conversation_id: conversationId ?? null }),
  })
  return parseJson<ChatResponse>(res)
}

async function sha256Hex(file: File): Promise<string> {
  const buf = await file.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest("SHA-256", buf)
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
}

export interface KPIResponse {
  total_conversations: number
  resolution_rate: number
  avg_response_time_ms: number
  patients_served: number
  escalation_rate: number
}

export interface VolumePoint {
  timestamp: string
  count: number
}

export interface CategoryPoint {
  category: string
  count: number
  percentage: number
}

export interface QuestionCount {
  question_preview: string
  count: number
}

export interface ConversationPage {
  items: ConversationResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ConversationResponse {
  id: string
  status: "ACTIVE" | "CLOSED" | "ESCALATED"
  started_at: string
}

export interface MessageResponse {
  id: string
  role: "USER" | "ASSISTANT" | "SYSTEM"
  content: string
  created_at: string
}

export interface DocumentPage {
  items: DocumentResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export interface DocumentResponse {
  id: string
  title: string
  type: string
  status: string
  chunks_count: number
  created_at: string
}

export interface SearchResult {
  chunk_id: string
  content: string
  score: number
  document_title: string
  metadata: Record<string, unknown>
}

export interface ReindexQueuedResponse {
  status: "queued"
}

export interface SettingResponse {
  id: number
  key: string
  value: Record<string, unknown>
  category: string
}

export interface ChatResponse {
  reply: string
  sources: Record<string, unknown>[]
  confidence: number
  escalated: boolean
  conversation_id: string
  response_time_ms: number
}
