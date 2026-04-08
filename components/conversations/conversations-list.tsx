"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"
import type { Conversation } from "@/app/conversations/page"

interface ConversationsListProps {
  conversations: Conversation[]
  selectedId: string | null
  onSelect: (id: string) => void
}

const statusConfig = {
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

function ListSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-2">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-4 w-full mb-1" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-16 mt-2" />
        </div>
      ))}
    </div>
  )
}

export function ConversationsList({
  conversations,
  selectedId,
  onSelect,
}: ConversationsListProps) {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <Card className="bg-card border-border h-full overflow-hidden">
      <CardContent className="p-0 h-full overflow-y-auto">
        {loading ? (
          <ListSkeleton />
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-12 text-center">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-muted-foreground"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <p className="text-sm text-muted-foreground">
              Nenhuma conversa encontrada
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Ajuste os filtros para ver mais resultados
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={cn(
                  "w-full text-left p-4 transition-colors hover:bg-muted/50",
                  selectedId === conv.id && "bg-primary/5 border-l-2 border-l-primary"
                )}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm text-foreground">
                    {conv.phone}
                  </span>
                  <Badge
                    variant="outline"
                    className={statusConfig[conv.status].className}
                  >
                    {statusConfig[conv.status].label}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                  {conv.lastMessage}
                </p>
                <span className="text-xs text-muted-foreground">
                  {conv.timestamp}
                </span>
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
