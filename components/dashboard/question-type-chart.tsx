"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"
import { Skeleton } from "@/components/ui/skeleton"
import { useState, useEffect } from "react"
import { ApiRequestError, fetchCategories } from "@/lib/api-client"

const COLORS: Record<string, string> = {
  agendamento: "#059669",
  procedimento: "#0EA5E9",
  preco: "#F59E0B",
  convenio: "#8B5CF6",
  emergencia: "#EC4899",
  outros: "#94A3B8",
}

const LABELS: Record<string, string> = {
  agendamento: "Agendamento",
  procedimento: "Procedimentos",
  preco: "Preços",
  convenio: "Convênios",
  emergencia: "Emergência",
  outros: "Outros",
}

export function QuestionTypeChart() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<{ name: string; value: number; color: string }[]>([])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const cats = await fetchCategories()
        if (!cancelled) {
          setData(
            cats.map((c) => ({
              name: LABELS[c.category] ?? c.category,
              value: Math.round(c.percentage),
              color: COLORS[c.category] ?? "#94A3B8",
            })),
          )
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof ApiRequestError ? e.message : "Erro ao carregar categorias")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground font-heading">
          Distribuição por tipo de pergunta (mensagens usuário)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <p className="text-sm text-destructive mb-2 border border-destructive/30 rounded-md p-2">{error}</p>
        )}
        {loading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : data.length === 0 && !error ? (
          <p className="text-sm text-muted-foreground py-12 text-center">Sem dados de categorias</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${entry.name}-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #E2E8F0",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                }}
                formatter={(value: number) => [`${value}%`, ""]}
              />
              <Legend
                layout="vertical"
                verticalAlign="middle"
                align="right"
                iconType="circle"
                iconSize={8}
                formatter={(value) => <span className="text-sm text-foreground">{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
