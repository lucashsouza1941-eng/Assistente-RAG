"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Skeleton } from "@/components/ui/skeleton"
import { useState, useEffect } from "react"

const data = [
  { hour: "00h", messages: 2 },
  { hour: "01h", messages: 1 },
  { hour: "02h", messages: 0 },
  { hour: "03h", messages: 0 },
  { hour: "04h", messages: 1 },
  { hour: "05h", messages: 3 },
  { hour: "06h", messages: 8 },
  { hour: "07h", messages: 15 },
  { hour: "08h", messages: 32 },
  { hour: "09h", messages: 45 },
  { hour: "10h", messages: 52 },
  { hour: "11h", messages: 48 },
  { hour: "12h", messages: 38 },
  { hour: "13h", messages: 42 },
  { hour: "14h", messages: 55 },
  { hour: "15h", messages: 58 },
  { hour: "16h", messages: 62 },
  { hour: "17h", messages: 54 },
  { hour: "18h", messages: 45 },
  { hour: "19h", messages: 32 },
  { hour: "20h", messages: 22 },
  { hour: "21h", messages: 15 },
  { hour: "22h", messages: 8 },
  { hour: "23h", messages: 4 },
]

export function MessageVolumeChart() {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1200)
    return () => clearTimeout(timer)
  }, [])

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground font-heading">
          Volume de Mensagens por Hora
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-[300px] w-full" />
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
              <YAxis
                tick={{ fontSize: 11, fill: "#64748B" }}
                tickLine={false}
                axisLine={false}
              />
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
