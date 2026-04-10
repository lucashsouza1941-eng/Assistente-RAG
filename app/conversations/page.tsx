"use client"

import { Suspense } from "react"
import { ConversationsContent } from "@/app/conversations/conversations-content"

export type { Conversation, Message } from "@/lib/types/conversations"

export default function ConversationsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-6 text-sm text-muted-foreground">Carregando conversas…</div>
      }
    >
      <ConversationsContent />
    </Suspense>
  )
}
