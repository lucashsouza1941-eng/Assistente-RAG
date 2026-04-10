"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, FileText } from "lucide-react"
import { useState } from "react"
import { ApiRequestError, searchKnowledge } from "@/lib/api-client"

export function SemanticSearch() {
  const [query, setQuery] = useState("")
  const [topK, setTopK] = useState(5)
  const [threshold, setThreshold] = useState(0.7)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<
    { chunk_id: string; content: string; document_title: string; score: number }[]
  >([])

  const handleSearch = async () => {
    if (!query.trim()) return
    setSearching(true)
    setError(null)
    try {
      const data = await searchKnowledge(query.trim(), topK, threshold)
      setResults(data)
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Erro na busca")
      setResults([])
    } finally {
      setSearching(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-primary bg-primary/10"
    if (score >= 0.6) return "text-yellow-600 bg-yellow-100"
    return "text-destructive bg-destructive/10"
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground font-heading">Busca semantica</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2 items-end">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Busque na base de conhecimento…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void handleSearch()}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2 text-xs">
            <label className="flex items-center gap-1">
              top_k
              <Input
                type="number"
                min={1}
                max={20}
                className="w-16 h-9"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
              />
            </label>
            <label className="flex items-center gap-1">
              min score
              <Input
                type="number"
                step={0.05}
                min={0}
                max={1}
                className="w-20 h-9"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
              />
            </label>
          </div>
          <Button onClick={() => void handleSearch()} disabled={!query.trim() || searching} className="bg-primary hover:bg-primary/90">
            {searching ? "Buscando…" : "Buscar"}
          </Button>
        </div>

        {error && <p className="text-sm text-destructive border border-destructive/30 rounded-md p-2">{error}</p>}

        {results.length > 0 && (
          <div className="space-y-3 max-h-[400px] overflow-y-auto">
            {results.map((result) => (
              <div key={result.chunk_id} className="p-4 border border-border rounded-lg hover:border-primary/30 transition-colors">
                <p className="text-sm text-foreground leading-relaxed mb-3 whitespace-pre-wrap">{result.content}</p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <FileText className="h-3.5 w-3.5" />
                    <span>{result.document_title}</span>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${getScoreColor(result.score)}`}>
                    {(result.score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {query && results.length === 0 && !searching && !error && (
          <div className="text-center py-8 text-muted-foreground">
            <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Nenhum resultado. Ajuste o limiar ou a consulta.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
