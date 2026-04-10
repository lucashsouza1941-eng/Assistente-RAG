"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageSquare, CheckCircle, Clock, TrendingUp, AlertTriangle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { useState, useEffect } from "react"
import { ApiRequestError, fetchKPIs, fetchTopQuestions, type KPIResponse } from "@/lib/api-client"

function KPICardSkeleton() {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-8 rounded-md" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-16 mb-1" />
        <Skeleton className="h-3 w-12" />
      </CardContent>
    </Card>
  )
}

function formatMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.round(ms)}ms`
}

export function DashboardKPIs() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [kpis, setKpis] = useState<KPIResponse | null>(null)
  const [topQuestions, setTopQuestions] = useState<{ question_preview: string; count: number }[]>([])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const [k, tq] = await Promise.all([fetchKPIs("7d"), fetchTopQuestions(5)])
        if (!cancelled) {
          setKpis(k)
          setTopQuestions(tq)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof ApiRequestError ? e.message : "Falha ao carregar indicadores")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <KPICardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (error || !kpis) {
    return (
      <p className="text-sm text-destructive border border-destructive/30 rounded-md p-3 bg-destructive/5">
        {error ?? "Sem dados"}
      </p>
    )
  }

  const cards = [
    { title: "Conversas (total)", value: String(kpis.total_conversations), icon: MessageSquare, sub: undefined as string | undefined },
    { title: "Taxa de resolução", value: `${Math.round(kpis.resolution_rate * 100)}%`, icon: CheckCircle, sub: "sem escalonamento" },
    { title: "Tempo medio de resposta", value: formatMs(kpis.avg_response_time_ms), icon: Clock, sub: undefined },
    { title: "Taxa de escalonamento", value: `${Math.round(kpis.escalation_rate * 100)}%`, icon: AlertTriangle, sub: undefined },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map((kpi) => (
        <Card key={kpi.title} className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{kpi.title}</CardTitle>
            <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/10">
              <kpi.icon className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground font-heading">{kpi.value}</div>
            {kpi.sub && <p className="text-xs text-muted-foreground">{kpi.sub}</p>}
            <div className="flex items-center gap-1 mt-1">
              <TrendingUp className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">API em tempo real</span>
            </div>
          </CardContent>
        </Card>
      ))}

      <Card className="bg-card border-border sm:col-span-2 lg:col-span-1">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Top 5 perguntas</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-1.5">
            {topQuestions.length === 0 ? (
              <li className="text-xs text-muted-foreground">Sem dados</li>
            ) : (
              topQuestions.map((q, index) => (
                <li key={`${q.question_preview}-${index}`} className="text-xs text-foreground truncate flex items-start gap-2">
                  <span className="text-primary font-semibold">{index + 1}.</span>
                  <span className="truncate" title={q.question_preview}>
                    {q.question_preview}
                  </span>
                </li>
              ))
            )}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
