"use client"

import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"

export function ReindexButton() {
  return (
    <div className="flex flex-col items-end gap-1 text-right max-w-sm">
      <Button type="button" variant="outline" disabled className="pointer-events-none opacity-70">
        <RefreshCw className="h-4 w-4 mr-2" />
        Reindexar por documento
      </Button>
      <p className="text-xs text-muted-foreground">
        Use o botao de reindexar em cada linha da tabela de documentos.
      </p>
    </div>
  )
}
