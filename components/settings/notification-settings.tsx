"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { CheckCircle, XCircle, Loader2 } from "lucide-react"
import { ApiRequestError, fetchSettings } from "@/lib/api-client"
import { Skeleton } from "@/components/ui/skeleton"
import { indexByKey, putScalarKey, unwrapSettingValue } from "@/lib/settings-values"

const DEFAULT_NOTIFICATIONS = {
  escalationEmail: "contato@odontovida.com.br",
  notifyLongWait: true,
  dailySummary: true,
  webhookUrl: "",
}

function mergeNotificationsLegacy(raw: unknown): typeof DEFAULT_NOTIFICATIONS {
  if (!raw || typeof raw !== "object") return DEFAULT_NOTIFICATIONS
  const v = raw as Record<string, unknown>
  return {
    escalationEmail:
      typeof v.escalationEmail === "string"
        ? v.escalationEmail
        : DEFAULT_NOTIFICATIONS.escalationEmail,
    notifyLongWait:
      typeof v.notifyLongWait === "boolean"
        ? v.notifyLongWait
        : DEFAULT_NOTIFICATIONS.notifyLongWait,
    dailySummary:
      typeof v.dailySummary === "boolean" ? v.dailySummary : DEFAULT_NOTIFICATIONS.dailySummary,
    webhookUrl: typeof v.webhookUrl === "string" ? v.webhookUrl : DEFAULT_NOTIFICATIONS.webhookUrl,
  }
}

function loadNotificationsFromRows(rows: ReturnType<typeof indexByKey>): typeof DEFAULT_NOTIFICATIONS {
  const hasGranular =
    rows.has("notifications.escalation_email") || rows.has("notifications.webhook_url")
  if (!hasGranular) {
    const legacy = rows.get("panel_notifications")
    if (legacy) {
      const u = unwrapSettingValue(legacy)
      if (u && typeof u === "object") return mergeNotificationsLegacy(u)
    }
  }

  const escalationEmail = unwrapSettingValue(rows.get("notifications.escalation_email"))
  const notifyLongWait = unwrapSettingValue(rows.get("notifications.notify_long_wait"))
  const dailySummary = unwrapSettingValue(rows.get("notifications.daily_summary"))
  const webhookUrl = unwrapSettingValue(rows.get("notifications.webhook_url"))

  return {
    escalationEmail:
      typeof escalationEmail === "string" ? escalationEmail : DEFAULT_NOTIFICATIONS.escalationEmail,
    notifyLongWait:
      typeof notifyLongWait === "boolean" ? notifyLongWait : DEFAULT_NOTIFICATIONS.notifyLongWait,
    dailySummary:
      typeof dailySummary === "boolean" ? dailySummary : DEFAULT_NOTIFICATIONS.dailySummary,
    webhookUrl: typeof webhookUrl === "string" ? webhookUrl : DEFAULT_NOTIFICATIONS.webhookUrl,
  }
}

export function NotificationSettings() {
  const [settings, setSettings] = useState(DEFAULT_NOTIFICATIONS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [webhookStatus, setWebhookStatus] = useState<"idle" | "testing" | "success" | "error">("idle")

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const rowsList = await fetchSettings("notifications")
        const rows = indexByKey(rowsList)
        if (!cancelled) setSettings(loadNotificationsFromRows(rows))
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
        putScalarKey("notifications.escalation_email", settings.escalationEmail),
        putScalarKey("notifications.notify_long_wait", settings.notifyLongWait),
        putScalarKey("notifications.daily_summary", settings.dailySummary),
        putScalarKey("notifications.webhook_url", settings.webhookUrl),
      ])
      toast.success("Configurações de notificações salvas")
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao salvar")
    }
  }

  const testWebhook = async () => {
    if (!settings.webhookUrl.trim()) {
      toast.error("Digite uma URL de webhook primeiro")
      return
    }

    setWebhookStatus("testing")
    try {
      const ctrl = new AbortController()
      const t = setTimeout(() => ctrl.abort(), 8000)
      const res = await fetch(settings.webhookUrl, {
        method: "HEAD",
        mode: "cors",
        signal: ctrl.signal,
      }).catch(() => null)
      clearTimeout(t)

      if (res && (res.ok || res.status === 405 || res.status === 404)) {
        setWebhookStatus("success")
        toast.success("URL respondeu (teste superficial)")
      } else if (res) {
        setWebhookStatus("error")
        toast.error(`Resposta HTTP ${res.status}`)
      } else {
        setWebhookStatus("error")
        toast.error("Não foi possível verificar a URL (CORS ou rede)")
      }
    } catch {
      setWebhookStatus("error")
      toast.error("Falha ao testar webhook")
    } finally {
      setTimeout(() => setWebhookStatus("idle"), 3000)
    }
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground font-heading">
          Configurações de Notificações
        </CardTitle>
        <CardDescription>
          Configure alertas e integrações externas
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <p className="text-sm text-destructive border border-destructive/30 rounded-md p-2">{error}</p>
        )}
        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : (
          <>
            <div className="space-y-2">
              <Label htmlFor="escalation-email">E-mail para Alertas de Escalonamento</Label>
              <Input
                id="escalation-email"
                type="email"
                value={settings.escalationEmail}
                onChange={(e) => setSettings({ ...settings, escalationEmail: e.target.value })}
                placeholder="email@exemplo.com"
              />
              <p className="text-xs text-muted-foreground">
                Receba um e-mail sempre que uma conversa for escalada para humano
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div>
                  <Label htmlFor="long-wait" className="font-medium">
                    {"Notificar quando paciente espera >5 min"}
                  </Label>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Receba alerta quando uma mensagem não for respondida em 5 minutos
                  </p>
                </div>
                <Switch
                  id="long-wait"
                  checked={settings.notifyLongWait}
                  onCheckedChange={(checked) => setSettings({ ...settings, notifyLongWait: checked })}
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div>
                  <Label htmlFor="daily-summary" className="font-medium">
                    Resumo diário por e-mail
                  </Label>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Receba um relatório diário com métricas de atendimento
                  </p>
                </div>
                <Switch
                  id="daily-summary"
                  checked={settings.dailySummary}
                  onCheckedChange={(checked) => setSettings({ ...settings, dailySummary: checked })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="webhook-url">Webhook URL para Integrações</Label>
              <div className="flex gap-2">
                <Input
                  id="webhook-url"
                  type="url"
                  value={settings.webhookUrl}
                  onChange={(e) => setSettings({ ...settings, webhookUrl: e.target.value })}
                  placeholder="https://exemplo.com/webhook"
                  className="flex-1"
                />
                <Button
                  variant="outline"
                  onClick={() => void testWebhook()}
                  disabled={webhookStatus === "testing"}
                  className="min-w-[100px]"
                >
                  {webhookStatus === "testing" && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  {webhookStatus === "success" && (
                    <CheckCircle className="h-4 w-4 mr-2 text-primary" />
                  )}
                  {webhookStatus === "error" && (
                    <XCircle className="h-4 w-4 mr-2 text-destructive" />
                  )}
                  {webhookStatus === "testing" ? "Testando..." : "Testar"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Envie eventos em tempo real para sistemas externos (CRM, Analytics, etc.)
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
