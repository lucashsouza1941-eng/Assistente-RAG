"use client"

import { AdminLayout } from "@/components/admin-layout"
import { ConversationsList } from "@/components/conversations/conversations-list"
import { ChatView } from "@/components/conversations/chat-view"
import { ConversationFilters } from "@/components/conversations/conversation-filters"
import { useState, useEffect, useCallback, useMemo } from "react"
import { useSearchParams } from "next/navigation"
import { ApiRequestError, fetchConversations, fetchMessages, type ConversationResponse } from "@/lib/api-client"
import { formatDistanceToNow } from "date-fns"
import { ptBR } from "date-fns/locale"
import type { Conversation, Message } from "@/lib/types/conversations"

function mapConvStatus(s: ConversationResponse["status"]): Conversation["status"] {
  if (s === "ACTIVE") return "active"
  if (s === "CLOSED") return "closed"
  return "escalated"
}

function periodToApi(p: string): "today" | "7d" | "30d" | undefined {
  if (p === "today") return "today"
  if (p === "7d") return "7d"
  if (p === "30d") return "30d"
  return undefined
}

function toUiConversation(c: ConversationResponse): Conversation {
  return {
    id: c.id,
    phone: `Ref. ${c.id.slice(0, 8)}…`,
    status: mapConvStatus(c.status),
    lastMessage: "Abra para ver o historico de mensagens",
    timestamp: formatDistanceToNow(new Date(c.started_at), { addSuffix: true, locale: ptBR }),
    questionType: "all",
  }
}

export function ConversationsContent() {
  const searchParams = useSearchParams()
  const idFromUrl = searchParams.get("id")

  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    period: "today",
    status: "all",
    questionType: "all",
  })
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)
  const [rawConversations, setRawConversations] = useState<ConversationResponse[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [msgLoading, setMsgLoading] = useState(false)
  const [msgError, setMsgError] = useState<string | null>(null)

  const loadList = useCallback(async () => {
    setListLoading(true)
    setListError(null)
    try {
      const period = periodToApi(filters.period)
      const page = await fetchConversations(1, 100, period)
      setRawConversations(page.items)
    } catch (e) {
      setListError(e instanceof ApiRequestError ? e.message : "Erro ao carregar conversas")
      setRawConversations([])
    } finally {
      setListLoading(false)
    }
  }, [filters.period])

  useEffect(() => {
    void loadList()
  }, [loadList])

  useEffect(() => {
    if (idFromUrl) setSelectedConversation(idFromUrl)
  }, [idFromUrl])

  const conversations = useMemo(() => {
    const ui = rawConversations.map(toUiConversation)
    return ui.filter((conv) => {
      if (filters.status !== "all" && conv.status !== filters.status) return false
      return true
    })
  }, [rawConversations, filters.status])

  useEffect(() => {
    if (conversations.length && !selectedConversation) {
      setSelectedConversation(conversations[0].id)
    }
  }, [conversations, selectedConversation])

  useEffect(() => {
    if (!selectedConversation) {
      setMessages([])
      return
    }
    let cancelled = false
    ;(async () => {
      setMsgLoading(true)
      setMsgError(null)
      try {
        const rows = await fetchMessages(selectedConversation)
        if (cancelled) return
        setMessages(
          rows.map((m) => ({
            id: m.id,
            type: m.role === "ASSISTANT" ? "bot" : "patient",
            content: m.content,
            timestamp: new Date(m.created_at).toLocaleTimeString("pt-BR", {
              hour: "2-digit",
              minute: "2-digit",
            }),
          })),
        )
      } catch (e) {
        if (!cancelled) {
          setMsgError(e instanceof ApiRequestError ? e.message : "Erro ao carregar mensagens")
          setMessages([])
        }
      } finally {
        if (!cancelled) setMsgLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedConversation])

  const selectedConv = conversations.find((c) => c.id === selectedConversation)

  return (
    <AdminLayout>
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        {listError && (
          <p className="text-sm text-destructive border border-destructive/30 rounded-md p-2 mb-2">{listError}</p>
        )}
        <ConversationFilters filters={filters} onFiltersChange={setFilters} />

        <div className="flex flex-1 mt-4 gap-4 overflow-hidden">
          <div className="w-full lg:w-2/5 overflow-hidden">
            <ConversationsList
              conversations={conversations}
              selectedId={selectedConversation}
              onSelect={setSelectedConversation}
              loading={listLoading}
            />
          </div>
          <div className="hidden lg:block lg:w-3/5 overflow-hidden">
            {msgError && (
              <p className="text-sm text-destructive border border-destructive/30 rounded-md p-2 mb-2">{msgError}</p>
            )}
            <ChatView conversation={selectedConv} messages={msgLoading ? [] : messages} loading={msgLoading} />
          </div>
        </div>
      </div>
    </AdminLayout>
  )
}
