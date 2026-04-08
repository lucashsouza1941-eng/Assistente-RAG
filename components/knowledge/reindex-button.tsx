"use client"

import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"
import { useState, useEffect } from "react"
import { toast } from "sonner"

export function ReindexButton() {
  const [isIndexing, setIsIndexing] = useState(false)
  const [progress, setProgress] = useState({ current: 0, total: 5 })

  const startReindex = () => {
    setIsIndexing(true)
    setProgress({ current: 0, total: 5 })
    toast.info("Iniciando re-indexação...")
  }

  useEffect(() => {
    if (!isIndexing) return

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev.current >= prev.total) {
          clearInterval(interval)
          setIsIndexing(false)
          toast.success("Re-indexação concluída!")
          return prev
        }
        return { ...prev, current: prev.current + 1 }
      })
    }, 1200)

    return () => clearInterval(interval)
  }, [isIndexing])

  return (
    <div className="flex flex-col items-end gap-2">
      <Button
        onClick={startReindex}
        disabled={isIndexing}
        variant={isIndexing ? "outline" : "default"}
        className={isIndexing ? "" : "bg-primary hover:bg-primary/90"}
      >
        <RefreshCw className={`h-4 w-4 mr-2 ${isIndexing ? "animate-spin" : ""}`} />
        {isIndexing ? "Re-indexando..." : "Re-indexar Tudo"}
      </Button>

      {isIndexing && (
        <div className="flex items-center gap-3 w-64">
          <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {progress.current} de {progress.total}
          </span>
        </div>
      )}
    </div>
  )
}
