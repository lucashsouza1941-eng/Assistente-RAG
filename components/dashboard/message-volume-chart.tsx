"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Skeleton } from "@/components/ui/skeleton"
import { useState, useEffect } from "react"
import { fetchVolume } from "@/lib/api-client"
import { ApiRequestError } from "@/lib/api-client"

export function MessageVolumeChart() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<{ hour: string; messages: number }[]>([])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const points = await fetchVolume("hour")
        if (!cancelled) {
          setData(
            points.map((p) => ({
              hour: p.timestamp.includes(":") ? `${p.timestamp.replace(":00", "")}h` : p.timestamp,
              messages: p.count,
            })),
          )
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof ApiRequestError ? e.message : "Erro ao carregar volume")
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
          Volume de mensagens por hora (últimos 7 dias)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <p className="text-sm text-destructive mb-2 border border-destructive/30 rounded-md p-2">{error}</p>
        )}
        {loading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : data.length === 0 && !error ? (
          <p className="text-sm text-muted-foreground py-12 text-center">Sem mensagens no período</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorMessages" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#059669" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 11, fill: "#64748B" }}
                tickLine={false}
                axisLine={{ stroke: "#E2E8F0" }}
                interval={2}
              />
              <YAxis tick={{ fontSize: 11, fill: "#64748B" }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #E2E8F0",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                }}
                labelStyle={{ color: "#1E293B", fontWeight: 600 }}
                formatter={(value: number) => [`${value} mensagens`, "Mensagens"]}
              />
              <Area
                type="monotone"
                dataKey="messages"
                stroke="#059669"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorMessages)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
