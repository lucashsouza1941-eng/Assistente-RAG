"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, FileText, X } from "lucide-react"
import { useState, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { ApiRequestError, uploadDocument } from "@/lib/api-client"

type DocType = "PROCEDURE" | "FAQ" | "PROTOCOL" | "GENERAL"

export function FileUpload({ onUploaded }: { onUploaded?: () => void }) {
  const [isDragging, setIsDragging] = useState(false)
  const [pending, setPending] = useState<{ file: File; type: DocType }[]>([])
  const [uploading, setUploading] = useState(false)

  const addFiles = (selectedFiles: File[]) => {
    const valid = selectedFiles.filter((file) => {
      const ext = "." + file.name.split(".").pop()?.toLowerCase()
      if (![".pdf", ".txt", ".docx"].includes(ext)) {
        toast.error(`Tipo nao suportado: ${file.name}`)
        return false
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error(`Arquivo muito grande: ${file.name}`)
        return false
      }
      return true
    })
    setPending((p) => [...p, ...valid.map((f) => ({ file: f, type: "GENERAL" as DocType }))])
  }

  const setType = (index: number, type: DocType) => {
    setPending((p) => p.map((row, i) => (i === index ? { ...row, type } : row)))
  }

  const removeAt = (index: number) => {
    setPending((p) => p.filter((_, i) => i !== index))
  }

  const uploadAll = async () => {
    setUploading(true)
    for (let i = 0; i < pending.length; i++) {
      const { file, type } = pending[i]
      const title = file.name.replace(/\.[^/.]+$/, "")
      try {
        await uploadDocument(file, title, type)
        toast.success(`Enviado: ${file.name}`)
        onUploaded?.()
      } catch (e) {
        toast.error(e instanceof ApiRequestError ? e.message : `Falha: ${file.name}`)
      }
    }
    setPending([])
    setUploading(false)
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    addFiles(Array.from(e.dataTransfer.files))
  }, [])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(Array.from(e.target.files))
  }, [])

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground font-heading">Upload de documentos</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
            isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50",
          )}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            multiple
            accept=".pdf,.txt,.docx"
            onChange={handleFileInput}
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="flex flex-col items-center gap-3">
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10">
                <Upload className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">Arraste arquivos ou clique para selecionar</p>
                <p className="text-xs text-muted-foreground mt-1">PDF, TXT, DOCX (max. 10MB)</p>
              </div>
            </div>
          </label>
        </div>

        {pending.length > 0 && (
          <div className="space-y-3">
            {pending.map((row, index) => (
              <div key={`${row.file.name}-${index}`} className="flex flex-wrap items-end gap-3 p-3 bg-muted/50 rounded-lg">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{row.file.name}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Tipo</Label>
                  <Select value={row.type} onValueChange={(v) => setType(index, v as DocType)}>
                    <SelectTrigger className="w-[180px] h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="GENERAL">Geral</SelectItem>
                      <SelectItem value="FAQ">FAQ</SelectItem>
                      <SelectItem value="PROCEDURE">Procedimento</SelectItem>
                      <SelectItem value="PROTOCOL">Protocolo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => removeAt(index)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button className="w-full" disabled={uploading} onClick={() => void uploadAll()}>
              {uploading ? "Enviando…" : `Enviar ${pending.length} arquivo(s)`}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
