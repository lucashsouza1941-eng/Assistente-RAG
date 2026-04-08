"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageSquare, CheckCircle, Clock, Users, TrendingUp } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { useState, useEffect } from "react"

const kpiData = [
  {
    title: "Conversas Hoje",
    value: "47",
    icon: MessageSquare,
    trend: "+12%",
    trendUp: true,
  },
  {
    title: "Taxa de Resolução",
    value: "84%",
    description: "sem humano",
    icon: CheckCircle,
    trend: "+3%",
    trendUp: true,
  },
  {
    title: "Tempo Médio de Resposta",
    value: "1.8s",
    icon: Clock,
    trend: "-0.2s",
    trendUp: true,
  },
  {
    title: "Pacientes no Mês",
    value: "312",
    icon: Users,
    trend: "+28",
    trendUp: true,
  },
]

const topQuestions = [
  "Como agendar uma consulta?",
  "Quais convênios são aceitos?",
  "Qual o valor da limpeza?",
  "Como funciona o clareamento?",
  "Vocês atendem emergência?",
]

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

export function DashboardKPIs() {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1000)
    return () => clearTimeout(timer)
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

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {kpiData.map((kpi) => (
        <Card key={kpi.title} className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {kpi.title}
            </CardTitle>
            <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/10">
              <kpi.icon className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground font-heading">
              {kpi.value}
            </div>
            {kpi.description && (
              <p className="text-xs text-muted-foreground">{kpi.description}</p>
            )}
            <div className="flex items-center gap-1 mt-1">
              <TrendingUp
                className={`h-3 w-3 ${
                  kpi.trendUp ? "text-primary" : "text-destructive"
                }`}
              />
              <span
                className={`text-xs font-medium ${
                  kpi.trendUp ? "text-primary" : "text-destructive"
                }`}
              >
                {kpi.trend}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Top 5 Questions Card */}
      <Card className="bg-card border-border sm:col-span-2 lg:col-span-1">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Top 5 Perguntas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-1.5">
            {topQuestions.map((question, index) => (
              <li
                key={index}
                className="text-xs text-foreground truncate flex items-start gap-2"
              >
                <span className="text-primary font-semibold">{index + 1}.</span>
                <span className="truncate">{question}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
