"use client"

import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ChevronDown, ChevronUp, User, FileText, Clock } from "lucide-react"
import { useState } from "react"
import type { Conversation, Message } from "@/app/conversations/page"

interface ChatViewProps {
  conversation?: Conversation
  messages: Message[]
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

function MessageBubble({ message }: { message: Message }) {
  const [showSources, setShowSources] = useState(false)
  const isBot = message.type === "bot"

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return "bg-primary"
    if (confidence >= 60) return "bg-yellow-500"
    return "bg-destructive"
  }

  return (
    <div className={cn("flex", isBot ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          isBot
            ? "bg-secondary text-secondary-foreground rounded-br-md"
            : "bg-muted text-foreground rounded-bl-md"
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <div
          className={cn(
            "flex items-center gap-2 mt-2 text-xs",
            isBot ? "text-secondary-foreground/70" : "text-muted-foreground"
          )}
        >
          <span>{message.timestamp}</span>
          
          {isBot && message.sources && message.sources.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSources(!showSources)}
              className={cn(
                "h-auto py-0.5 px-2 text-xs",
                isBot ? "text-secondary-foreground/70 hover:text-secondary-foreground hover:bg-secondary-foreground/10" : ""
              )}
            >
              Ver fontes
              {showSources ? (
                <ChevronUp className="h-3 w-3 ml-1" />
              ) : (
                <ChevronDown className="h-3 w-3 ml-1" />
              )}
            </Button>
          )}
        </div>

        {message.escalated && (
          <div className="flex items-center gap-2 mt-3 p-2 bg-destructive/10 rounded-lg">
            <User className="h-4 w-4 text-destructive" />
            <span className="text-xs font-medium text-destructive">
              Escalado para Humano
            </span>
          </div>
        )}

        {showSources && message.sources && (
          <div className="mt-3 space-y-2 pt-3 border-t border-secondary-foreground/20">
            <p className="text-xs font-medium text-secondary-foreground/80">
              Fontes utilizadas:
            </p>
            {message.sources.map((source, index) => (
              <div
                key={index}
                className="p-2 bg-secondary-foreground/10 rounded-lg"
              >
                <div className="flex items-center gap-2 mb-1">
                  <FileText className="h-3 w-3" />
                  <span className="text-xs font-medium">{source.document}</span>
                </div>
                <p className="text-xs opacity-80 line-clamp-2">{source.text}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs">Confiança:</span>
                  <div className="flex-1 h-1.5 bg-secondary-foreground/20 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all",
                        getConfidenceColor(source.confidence)
                      )}
                      style={{ width: `${source.confidence}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium">{source.confidence}%</span>
                </div>
              </div>
            ))}
            {message.responseTime && (
              <div className="flex items-center gap-1 text-xs opacity-70">
                <Clock className="h-3 w-3" />
                <span>Tempo de resposta: {message.responseTime}ms</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export function ChatView({ conversation, messages }: ChatViewProps) {
  if (!conversation) {
    return (
      <Card className="bg-card border-border h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
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
            Selecione uma conversa para visualizar
          </p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="bg-card border-border h-full flex flex-col overflow-hidden">
      <CardHeader className="border-b border-border py-4 px-6 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-foreground">{conversation.phone}</h3>
            <p className="text-xs text-muted-foreground">{conversation.timestamp}</p>
          </div>
          <Badge
            variant="outline"
            className={statusConfig[conversation.status].className}
          >
            {statusConfig[conversation.status].label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-6">
        <div className="space-y-4">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
