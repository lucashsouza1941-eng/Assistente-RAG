"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { toast } from "sonner"
import { CheckCircle, XCircle, Loader2 } from "lucide-react"

export function NotificationSettings() {
  const [settings, setSettings] = useState({
    escalationEmail: "contato@odontovida.com.br",
    notifyLongWait: true,
    dailySummary: true,
    webhookUrl: "",
  })
  const [webhookStatus, setWebhookStatus] = useState<"idle" | "testing" | "success" | "error">("idle")

  const handleSave = () => {
    toast.success("Configurações de notificações salvas!")
  }

  const testWebhook = () => {
    if (!settings.webhookUrl) {
      toast.error("Digite uma URL de webhook primeiro")
      return
    }
    
    setWebhookStatus("testing")
    setTimeout(() => {
      // Simulate webhook test
      const success = Math.random() > 0.3
      setWebhookStatus(success ? "success" : "error")
      
      if (success) {
        toast.success("Webhook testado com sucesso!")
      } else {
        toast.error("Falha ao testar webhook")
      }
      
      setTimeout(() => setWebhookStatus("idle"), 3000)
    }, 1500)
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
              onClick={testWebhook}
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

        <Button onClick={handleSave} className="w-full bg-primary hover:bg-primary/90">
          Salvar Configurações
        </Button>
      </CardContent>
    </Card>
  )
}
