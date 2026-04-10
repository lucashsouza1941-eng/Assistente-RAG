"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useState, useEffect } from "react"
import Link from "next/link"
import { fetchConversations } from "@/lib/api-client"
import { ApiRequestError } from "@/lib/api-client"
import { formatDistanceToNow } from "date-fns"
import { ptBR } from "date-fns/locale"

type ConversationStatus = "active" | "closed" | "escalated"

function mapStatus(s: string): ConversationStatus {
  if (s === "ACTIVE") return "active"
  if (s === "CLOSED") return "closed"
  return "escalated"
}

const statusConfig: Record<
  ConversationStatus,
  { label: string; className: string }
> = {
  active: {
    label: "Ativo",
    className: "bg-primary/10 text-primary border-primary/20",
  },
  closed: {
    label: "Encerrado",
    className: "bg-muted text-muted-foreground border-border",
  },
  escalated: {
    label: "Escalado",
    className: "bg-orange-100 text-orange-700 border-orange-200",
  },
}

function ConversationSkeleton() {
  return (
    <div className="flex items-center justify-between p-4 border-b border-border last:border-b-0">
      <div className="flex-1 min-w-0 space-y-2">
        <div className="flex items-center gap-3">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="h-4 w-3/4" />
      </div>
      <Skeleton className="h-4 w-16" />
    </div>
  )
}

export function RecentConversations() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<
    { id: string; status: ConversationStatus; startedAt: string; label: string }[]
  >([])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const page = await fetchConversations(1, 10, "7d")
        if (!cancelled) {
          setItems(
            page.items.map((c) => ({
              id: c.id,
              status: mapStatus(c.status),
              startedAt: c.started_at,
              label: `Conv. ${c.id.slice(0, 8)}…`,
            })),
          )
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof ApiRequestError ? e.message : "Erro ao carregar conversas")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <Card className="bg-card border-border">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold text-foreground font-heading">Últimas conversas</CardTitle>
        <Link href="/conversations" className="text-sm text-primary hover:text-primary/80 font-medium">
          Ver todas
        </Link>
      </CardHeader>
      <CardContent className="p-0">
        {error && (
          <p className="text-sm text-destructive p-4 border-b border-border">{error}</p>
        )}
        {loading ? (
          <div className="divide-y divide-border">
            {Array.from({ length: 5 }).map((_, i) => (
              <ConversationSkeleton key={i} />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground p-6 text-center">Nenhuma conversa no período</p>
        ) : (
          <div className="divide-y divide-border">
            {items.map((conv) => (
              <Link
                key={conv.id}
                href={`/conversations?id=${conv.id}`}
                className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-medium text-sm text-foreground">{conv.label}</span>
                    <Badge variant="outline" className={statusConfig[conv.status].className}>
                      {statusConfig[conv.status].label}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground truncate">Iniciada em {conv.startedAt.slice(0, 16).replace("T", " ")}</p>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                  {formatDistanceToNow(new Date(conv.startedAt), { addSuffix: true, locale: ptBR })}
                </span>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
