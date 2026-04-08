"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, FileText, ExternalLink } from "lucide-react"
import { useState } from "react"

interface SearchResult {
  id: string
  text: string
  source: string
  score: number
}

const mockResults: SearchResult[] = [
  {
    id: "1",
    text: "O clareamento dental é um procedimento estético que utiliza gel à base de peróxido de hidrogênio ou carbamida para clarear os dentes. O tratamento pode ser realizado no consultório ou em casa, com moldeiras personalizadas.",
    source: "Tabela de Procedimentos 2024.pdf",
    score: 94,
  },
  {
    id: "2",
    text: "Recomendamos evitar alimentos com corantes fortes (café, vinho tinto, molho de tomate) nas primeiras 48 horas após o clareamento. A sensibilidade dental temporária é normal e diminui em poucos dias.",
    source: "Protocolo Pós-Operatório.pdf",
    score: 87,
  },
  {
    id: "3",
    text: "O clareamento a laser tem duração de aproximadamente 1 hora por sessão. Normalmente são necessárias de 1 a 3 sessões para obter o resultado desejado, dependendo do grau de escurecimento dos dentes.",
    source: "FAQ Convênios.docx",
    score: 72,
  },
]

export function SemanticSearch() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)

  const handleSearch = () => {
    if (!query.trim()) return
    
    setSearching(true)
    // Simulate search delay
    setTimeout(() => {
      setResults(mockResults)
      setSearching(false)
    }, 800)
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-primary bg-primary/10"
    if (score >= 60) return "text-yellow-600 bg-yellow-100"
    return "text-destructive bg-destructive/10"
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground font-heading">
          Busca Semântica
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Busque na base de conhecimento..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="pl-10"
            />
          </div>
          <Button
            onClick={handleSearch}
            disabled={!query.trim() || searching}
            className="bg-primary hover:bg-primary/90"
          >
            {searching ? "Buscando..." : "Buscar"}
          </Button>
        </div>

        {results.length > 0 && (
          <div className="space-y-3 max-h-[400px] overflow-y-auto">
            {results.map((result) => (
              <div
                key={result.id}
                className="p-4 border border-border rounded-lg hover:border-primary/30 transition-colors"
              >
                <p className="text-sm text-foreground leading-relaxed mb-3">
                  {result.text}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <FileText className="h-3.5 w-3.5" />
                    <span>{result.source}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded ${getScoreColor(
                        result.score
                      )}`}
                    >
                      {result.score}%
                    </span>
                    <Button variant="ghost" size="sm" className="h-7 text-xs">
                      <ExternalLink className="h-3.5 w-3.5 mr-1" />
                      Ver contexto
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {query && results.length === 0 && !searching && (
          <div className="text-center py-8 text-muted-foreground">
            <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Digite sua busca e pressione Enter</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
