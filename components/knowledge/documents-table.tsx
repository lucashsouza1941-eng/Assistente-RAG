"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Eye, Trash2, Loader2 } from "lucide-react"
import { useState, useEffect } from "react"

type DocumentType = "procedure" | "faq" | "protocol" | "pricing"
type DocumentStatus = "indexed" | "processing" | "error"

interface Document {
  id: string
  name: string
  type: DocumentType
  chunks: number
  status: DocumentStatus
  updatedAt: string
}

const documents: Document[] = [
  {
    id: "1",
    name: "Tabela de Procedimentos 2024.pdf",
    type: "procedure",
    chunks: 45,
    status: "indexed",
    updatedAt: "15 Mar 2024",
  },
  {
    id: "2",
    name: "FAQ Convênios.docx",
    type: "faq",
    chunks: 28,
    status: "indexed",
    updatedAt: "12 Mar 2024",
  },
  {
    id: "3",
    name: "Protocolo Pós-Operatório.pdf",
    type: "protocol",
    chunks: 32,
    status: "processing",
    updatedAt: "10 Mar 2024",
  },
  {
    id: "4",
    name: "Preços Particulares.xlsx",
    type: "pricing",
    chunks: 18,
    status: "indexed",
    updatedAt: "08 Mar 2024",
  },
  {
    id: "5",
    name: "Perguntas Frequentes.txt",
    type: "faq",
    chunks: 0,
    status: "error",
    updatedAt: "05 Mar 2024",
  },
]

const typeConfig: Record<DocumentType, { label: string; className: string }> = {
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
  pricing: {
    label: "Preços",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
}

const statusConfig: Record<DocumentStatus, { label: string; className: string; icon?: React.ReactNode }> = {
  indexed: {
    label: "Indexado",
    className: "bg-primary/10 text-primary border-primary/20",
  },
  processing: {
    label: "Processando",
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

export function DocumentsTable() {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1200)
    return () => clearTimeout(timer)
  }, [])

  return (
    <Card className="bg-card border-border overflow-hidden">
      <CardContent className="p-0">
        {loading ? (
          <TableSkeleton />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                    Nome do Arquivo
                  </th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                    Tipo
                  </th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                    Chunks
                  </th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                    Status
                  </th>
                  <th className="text-left text-xs font-medium text-muted-foreground px-4 py-3">
                    Última Atualização
                  </th>
                  <th className="text-right text-xs font-medium text-muted-foreground px-4 py-3">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-foreground">
                        {doc.name}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className={typeConfig[doc.type].className}>
                        {typeConfig[doc.type].label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground">
                        {doc.chunks}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className={`flex items-center gap-1 w-fit ${statusConfig[doc.status].className}`}>
                        {statusConfig[doc.status].icon}
                        {statusConfig[doc.status].label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground">
                        {doc.updatedAt}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <Eye className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
