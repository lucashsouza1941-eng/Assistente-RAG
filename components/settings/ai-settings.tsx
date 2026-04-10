"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { ApiRequestError, fetchSettings, updateSetting } from "@/lib/api-client"
import { Skeleton } from "@/components/ui/skeleton"

const DEFAULT_AI = {
  model: "gpt-4o",
  temperature: 0.3,
  maxTokens: 500,
  confidenceThreshold: 70,
}

function mergeAiValue(raw: unknown): typeof DEFAULT_AI {
  if (!raw || typeof raw !== "object") return DEFAULT_AI
  const v = raw as Record<string, unknown>
  return {
    ...DEFAULT_AI,
    model: typeof v.model === "string" ? v.model : DEFAULT_AI.model,
    temperature:
      typeof v.temperature === "number" ? v.temperature : DEFAULT_AI.temperature,
    maxTokens: typeof v.maxTokens === "number" ? v.maxTokens : DEFAULT_AI.maxTokens,
    confidenceThreshold:
      typeof v.confidenceThreshold === "number"
        ? v.confidenceThreshold
        : DEFAULT_AI.confidenceThreshold,
  }
}

export function AISettings() {
  const [settings, setSettings] = useState(DEFAULT_AI)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const rows = await fetchSettings("ai")
        const row = rows.find((r) => r.key === "panel_ai")
        if (!cancelled && row?.value) {
          setSettings(mergeAiValue(row.value))
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiRequestError ? e.message : "Erro ao carregar")
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const handleSave = async () => {
    try {
      await updateSetting("panel_ai", settings as unknown as Record<string, unknown>)
      toast.success("Configurações de IA salvas")
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao salvar")
    }
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground font-heading">
          Configurações de IA
        </CardTitle>
        <CardDescription>
          Ajuste os parâmetros do modelo de linguagem
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <p className="text-sm text-destructive border border-destructive/30 rounded-md p-2">{error}</p>
        )}
        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : (
          <>
            <div className="space-y-2">
              <Label htmlFor="model">Modelo</Label>
              <Select
                value={settings.model}
                onValueChange={(value) => setSettings({ ...settings, model: value })}
              >
                <SelectTrigger id="model">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                  <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                  <SelectItem value="claude-3-5-sonnet">Claude 3.5 Sonnet</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                GPT-4o oferece melhor qualidade, enquanto GPT-4o Mini é mais rápido e econômico
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Temperatura</Label>
                <span className="text-sm font-medium text-foreground">
                  {settings.temperature.toFixed(1)}
                </span>
              </div>
              <Slider
                value={[settings.temperature]}
                onValueChange={([value]) => setSettings({ ...settings, temperature: value })}
                min={0}
                max={1}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Valores mais baixos geram respostas mais consistentes, valores mais altos são mais criativos
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-tokens">Máximo de Tokens</Label>
              <Input
                id="max-tokens"
                type="number"
                value={settings.maxTokens}
                onChange={(e) =>
                  setSettings({ ...settings, maxTokens: parseInt(e.target.value, 10) || 0 })
                }
                min={100}
                max={4000}
              />
              <p className="text-xs text-muted-foreground">
                Limite o tamanho máximo das respostas (1 token ≈ 4 caracteres)
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Threshold de Confiança para Escalonamento</Label>
                <span className="text-sm font-medium text-foreground">
                  {settings.confidenceThreshold}%
                </span>
              </div>
              <Slider
                value={[settings.confidenceThreshold]}
                onValueChange={([value]) => setSettings({ ...settings, confidenceThreshold: value })}
                min={0}
                max={100}
                step={5}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Se a confiança da resposta for menor que este valor, a conversa será escalada para um humano
              </p>
            </div>

            <Button onClick={() => void handleSave()} className="w-full bg-primary hover:bg-primary/90">
              Salvar Configurações
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  )
}
