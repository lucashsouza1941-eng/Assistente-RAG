"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Eye, Trash2, Loader2, RefreshCw } from "lucide-react"
import { useState, useEffect, useCallback } from "react"
import { ApiRequestError, deleteDocument, fetchDocuments, reindexDocument, type DocumentResponse } from "@/lib/api-client"
import { toast } from "sonner"

type DocumentTypeUi = "procedure" | "faq" | "protocol" | "general"

function mapType(t: string): DocumentTypeUi {
  const x = t.toUpperCase()
  if (x === "PROCEDURE") return "procedure"
  if (x === "FAQ") return "faq"
  if (x === "PROTOCOL") return "protocol"
  return "general"
}

function mapStatus(s: string): "indexed" | "processing" | "error" | "pending" {
  const x = s.toUpperCase()
  if (x === "INDEXED") return "indexed"
  if (x === "PROCESSING" || x === "PENDING") return "processing"
  if (x === "ERROR") return "error"
  return "pending"
}

const typeConfig: Record<DocumentTypeUi, { label: string; className: string }> = {
  procedure: {
    label: "Procedimento",
    className: "bg-primary/10 text-primary border-primary/20",
  },
  faq: {
    label: "FAQ",
    className: "bg-secondary/10 text-secondary border-secondary/20",
  },
  protocol: {
    label: "Protocolo",
    className: "bg-purple-100 text-purple-700 border-purple-200",
  },
  general: {
    label: "Geral",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
}

const statusConfig = {
  indexed: {
    label: "Indexado",
    className: "bg-primary/10 text-primary border-primary/20",
  },
  processing: {
    label: "Processando",
    className: "bg-yellow-100 text-yellow-700 border-yellow-200",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  pending: {
    label: "Pendente",
    className: "bg-yellow-100 text-yellow-700 border-yellow-200",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  error: {
    label: "Erro",
    className: "bg-destructive/10 text-destructive border-destructive/20",
  },
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 border-b border-border">
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-12" />
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-20" />
        </div>
      ))}
    </div>
  )
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })
  } catch {
    return iso
  }
}

export function DocumentsTable({ onRefresh }: { onRefresh?: () => void }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [documents, setDocuments] = useState<DocumentResponse[]>([])
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const page = await fetchDocuments(1, 100)
      setDocuments(page.items)
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Erro ao listar documentos")
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handleDelete = async (id: string) => {
    if (!confirm("Excluir este documento?")) return
    setBusyId(id)
    try {
      await deleteDocument(id)
      toast.success("Documento removido")
      await load()
      onRefresh?.()
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao excluir")
    } finally {
      setBusyId(null)
    }
  }

  const handleReindex = async (id: string) => {
    setBusyId(id)
    try {
      await reindexDocument(id)
      toast.success("Reindexacao enfileirada")
      await load()
      onRefresh?.()
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao reindexar")
    } finally {
      setBusyId(null)
    }
  }

  return (
    <Card className="bg-card border-border overflow-hidden">
      <CardContent className="p-0">
        {error && (
          <p className="text-sm text-destructive p-4 border-b border-border">{error}</p>
        )}
        {loading ? (
          <TableSkeleton />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Titulo</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Tipo</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Chunks</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">Criado</th>
                  <th className="text-right text-xs font-medium text-muted-foreground px-4 py-3">Acoes</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => {
                  const tu = mapType(doc.type)
                  const su = mapStatus(doc.status)
                  const sc = statusConfig[su as keyof typeof statusConfig] ?? statusConfig.processing
                  return (
                    <tr key={doc.id} className="border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-sm font-medium text-foreground">{doc.title}</span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className={typeConfig[tu].className}>
                          {typeConfig[tu].label}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-muted-foreground">{doc.chunks_count}</span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className={`flex items-center gap-1 w-fit ${sc.className}`}>
                          {"icon" in sc ? sc.icon : null}
                          {sc.label}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-muted-foreground">{formatDate(doc.created_at)}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            title="Reindexar"
                            disabled={busyId === doc.id}
                            onClick={() => void handleReindex(doc.id)}
                          >
                            <RefreshCw className="h-4 w-4 text-muted-foreground" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8" disabled title="Visualizar em breve">
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            disabled={busyId === doc.id}
                            onClick={() => void handleDelete(doc.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
