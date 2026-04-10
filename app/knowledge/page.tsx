"use client"

import { useState, useCallback } from "react"
import { AdminLayout } from "@/components/admin-layout"
import { DocumentsTable } from "@/components/knowledge/documents-table"
import { FileUpload } from "@/components/knowledge/file-upload"
import { FAQEditor } from "@/components/knowledge/faq-editor"
import { SemanticSearch } from "@/components/knowledge/semantic-search"
import { ReindexButton } from "@/components/knowledge/reindex-button"

export default function KnowledgePage() {
  const [tableKey, setTableKey] = useState(0)
  const refresh = useCallback(() => setTableKey((k) => k + 1), [])

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground font-heading">Documentos indexados</h2>
            <p className="text-sm text-muted-foreground">Gerencie os documentos que alimentam a base de conhecimento do bot</p>
          </div>
          <ReindexButton />
        </div>

        <DocumentsTable key={tableKey} onRefresh={refresh} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FileUpload onUploaded={refresh} />
          <SemanticSearch />
        </div>

        <FAQEditor />
      </div>
    </AdminLayout>
  )
}
