"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { ApiRequestError, fetchSettings } from "@/lib/api-client"
import { Skeleton } from "@/components/ui/skeleton"
import { indexByKey, putScalarKey, unwrapSettingValue } from "@/lib/settings-values"

const DEFAULT_BOT = {
  name: "Dra. Sofia — Assistente Virtual",
  welcomeMessage: "Olá! Sou a Dra. Sofia, assistente virtual da Clínica OdontoVida. Como posso ajudar você hoje?",
  closingMessage: "Obrigada pelo contato! Se precisar de mais alguma informação, é só me chamar. Tenha um ótimo dia!",
  respondOutsideHours: false,
  startTime: "08:00",
  endTime: "18:00",
  workDays: {
    seg: true,
    ter: true,
    qua: true,
    qui: true,
    sex: true,
    sab: false,
    dom: false,
  },
}

function mergeBotLegacy(raw: unknown): typeof DEFAULT_BOT {
  if (!raw || typeof raw !== "object") return DEFAULT_BOT
  const v = raw as Record<string, unknown>
  const workDays =
    v.workDays && typeof v.workDays === "object"
      ? { ...DEFAULT_BOT.workDays, ...(v.workDays as Record<string, boolean>) }
      : DEFAULT_BOT.workDays
  return { ...DEFAULT_BOT, ...v, workDays } as typeof DEFAULT_BOT
}

function loadBotFromRows(rows: ReturnType<typeof indexByKey>): typeof DEFAULT_BOT {
  const hasGranular =
    rows.has("bot.clinic_name") ||
    rows.has("bot.welcome_message") ||
    rows.has("bot.closing_message")
  if (!hasGranular) {
    const legacy = rows.get("panel_bot")
    if (legacy) {
      const u = unwrapSettingValue(legacy)
      if (u && typeof u === "object") return mergeBotLegacy(u)
    }
  }

  const clinicName = unwrapSettingValue(rows.get("bot.clinic_name"))
  const welcome = unwrapSettingValue(rows.get("bot.welcome_message"))
  const closing = unwrapSettingValue(rows.get("bot.closing_message"))
  const outside = unwrapSettingValue(rows.get("bot.respond_outside_hours"))
  const start = unwrapSettingValue(rows.get("bot.business_hours_start"))
  const end = unwrapSettingValue(rows.get("bot.business_hours_end"))
  const wd = unwrapSettingValue(rows.get("bot.work_days"))

  let workDays = DEFAULT_BOT.workDays
  if (wd && typeof wd === "object") {
    workDays = { ...DEFAULT_BOT.workDays, ...(wd as Record<string, boolean>) }
  }

  return {
    name: typeof clinicName === "string" ? clinicName : DEFAULT_BOT.name,
    welcomeMessage: typeof welcome === "string" ? welcome : DEFAULT_BOT.welcomeMessage,
    closingMessage: typeof closing === "string" ? closing : DEFAULT_BOT.closingMessage,
    respondOutsideHours: typeof outside === "boolean" ? outside : DEFAULT_BOT.respondOutsideHours,
    startTime: typeof start === "string" ? start : DEFAULT_BOT.startTime,
    endTime: typeof end === "string" ? end : DEFAULT_BOT.endTime,
    workDays,
  }
}

export function BotSettings() {
  const [settings, setSettings] = useState(DEFAULT_BOT)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const rowsList = await fetchSettings("bot")
        const rows = indexByKey(rowsList)
        if (!cancelled) setSettings(loadBotFromRows(rows))
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
      await Promise.all([
        putScalarKey("bot.clinic_name", settings.name),
        putScalarKey("bot.welcome_message", settings.welcomeMessage),
        putScalarKey("bot.closing_message", settings.closingMessage),
        putScalarKey("bot.respond_outside_hours", settings.respondOutsideHours),
        putScalarKey("bot.business_hours_start", settings.startTime),
        putScalarKey("bot.business_hours_end", settings.endTime),
        putScalarKey("bot.work_days", settings.workDays),
      ])
      toast.success("Configurações do bot salvas")
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao salvar")
    }
  }

  const toggleWorkDay = (day: keyof typeof settings.workDays) => {
    setSettings({
      ...settings,
      workDays: {
        ...settings.workDays,
        [day]: !settings.workDays[day],
      },
    })
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground font-heading">
          Configurações do Bot
        </CardTitle>
        <CardDescription>
          Personalize as mensagens e comportamento do assistente
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <p className="text-sm text-destructive border border-destructive/30 rounded-md p-2">{error}</p>
        )}
        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <>
            <div className="space-y-2">
              <Label htmlFor="bot-name">Nome do Assistente</Label>
              <Input
                id="bot-name"
                value={settings.name}
                onChange={(e) => setSettings({ ...settings, name: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="welcome-message">Mensagem de Boas-vindas</Label>
              <Textarea
                id="welcome-message"
                value={settings.welcomeMessage}
                onChange={(e) => setSettings({ ...settings, welcomeMessage: e.target.value })}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="closing-message">Mensagem de Encerramento</Label>
              <Textarea
                id="closing-message"
                value={settings.closingMessage}
                onChange={(e) => setSettings({ ...settings, closingMessage: e.target.value })}
                rows={3}
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
              <div>
                <Label htmlFor="outside-hours" className="font-medium">
                  Responder fora do horário comercial
                </Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  O bot responderá mensagens mesmo fora do expediente
                </p>
              </div>
              <Switch
                id="outside-hours"
                checked={settings.respondOutsideHours}
                onCheckedChange={(checked) => setSettings({ ...settings, respondOutsideHours: checked })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start-time">Horário de Início</Label>
                <Input
                  id="start-time"
                  type="time"
                  value={settings.startTime}
                  onChange={(e) => setSettings({ ...settings, startTime: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end-time">Horário de Fim</Label>
                <Input
                  id="end-time"
                  type="time"
                  value={settings.endTime}
                  onChange={(e) => setSettings({ ...settings, endTime: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-3">
              <Label>Dias de Funcionamento</Label>
              <div className="flex flex-wrap gap-4">
                {[
                  { key: "seg", label: "Seg" },
                  { key: "ter", label: "Ter" },
                  { key: "qua", label: "Qua" },
                  { key: "qui", label: "Qui" },
                  { key: "sex", label: "Sex" },
                  { key: "sab", label: "Sáb" },
                  { key: "dom", label: "Dom" },
                ].map((day) => (
                  <div key={day.key} className="flex items-center gap-2">
                    <Checkbox
                      id={`day-${day.key}`}
                      checked={settings.workDays[day.key as keyof typeof settings.workDays]}
                      onCheckedChange={() => toggleWorkDay(day.key as keyof typeof settings.workDays)}
                    />
                    <Label htmlFor={`day-${day.key}`} className="text-sm cursor-pointer">
                      {day.label}
                    </Label>
                  </div>
                ))}
              </div>
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
