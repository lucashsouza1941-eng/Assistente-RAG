"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useState, useEffect } from "react"
import Link from "next/link"

type ConversationStatus = "active" | "closed" | "escalated"

interface Conversation {
  id: string
  phone: string
  lastMessage: string
  status: ConversationStatus
  timestamp: string
}

const conversations: Conversation[] = [
  {
    id: "1",
    phone: "(11) 9****-3847",
    lastMessage: "Obrigado! Vou comparecer no horário marcado.",
    status: "closed",
    timestamp: "há 5 min",
  },
  {
    id: "2",
    phone: "(11) 9****-2156",
    lastMessage: "Quanto custa o clareamento dental?",
    status: "active",
    timestamp: "há 8 min",
  },
  {
    id: "3",
    phone: "(21) 9****-7823",
    lastMessage: "Preciso falar com um dentista urgente!",
    status: "escalated",
    timestamp: "há 12 min",
  },
  {
    id: "4",
    phone: "(11) 9****-4521",
    lastMessage: "Vocês aceitam Unimed?",
    status: "active",
    timestamp: "há 15 min",
  },
  {
    id: "5",
    phone: "(19) 9****-8932",
    lastMessage: "Perfeito, agendado para quinta às 14h.",
    status: "closed",
    timestamp: "há 22 min",
  },
  {
    id: "6",
    phone: "(11) 9****-1098",
    lastMessage: "Como funciona o tratamento de canal?",
    status: "active",
    timestamp: "há 28 min",
  },
  {
    id: "7",
    phone: "(21) 9****-5467",
    lastMessage: "Estou com muita dor no dente.",
    status: "escalated",
    timestamp: "há 35 min",
  },
  {
    id: "8",
    phone: "(11) 9****-3214",
    lastMessage: "Qual o valor da consulta particular?",
    status: "closed",
    timestamp: "há 42 min",
  },
  {
    id: "9",
    phone: "(11) 9****-6789",
    lastMessage: "Posso parcelar o implante?",
    status: "active",
    timestamp: "há 1h",
  },
  {
    id: "10",
    phone: "(19) 9****-4356",
    lastMessage: "Obrigada pelas informações!",
    status: "closed",
    timestamp: "há 1h",
  },
]

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

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1600)
    return () => clearTimeout(timer)
  }, [])

  return (
    <Card className="bg-card border-border">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold text-foreground font-heading">
          Últimas Conversas
        </CardTitle>
        <Link
          href="/conversations"
          className="text-sm text-primary hover:text-primary/80 font-medium"
        >
          Ver todas
        </Link>
      </CardHeader>
      <CardContent className="p-0">
        {loading ? (
          <div className="divide-y divide-border">
            {Array.from({ length: 5 }).map((_, i) => (
              <ConversationSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-border">
            {conversations.map((conv) => (
              <Link
                key={conv.id}
                href={`/conversations?id=${conv.id}`}
                className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
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
                  <p className="text-sm text-muted-foreground truncate">
                    {conv.lastMessage}
                  </p>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                  {conv.timestamp}
                </span>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
