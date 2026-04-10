"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Smartphone, QrCode, RefreshCw } from "lucide-react"
import { useState, useEffect } from "react"
import { toast } from "sonner"
import { ApiRequestError, fetchSettings, updateSetting } from "@/lib/api-client"
import { Skeleton } from "@/components/ui/skeleton"

const DEFAULT_WHATSAPP = {
  phone: "(11) 98765-4321",
  isConnected: true,
  lastSyncLabel: "há 5 minutos",
}

function mergeWhatsappValue(raw: unknown): typeof DEFAULT_WHATSAPP {
  if (!raw || typeof raw !== "object") return DEFAULT_WHATSAPP
  const v = raw as Record<string, unknown>
  return {
    phone: typeof v.phone === "string" ? v.phone : DEFAULT_WHATSAPP.phone,
    isConnected:
      typeof v.isConnected === "boolean" ? v.isConnected : DEFAULT_WHATSAPP.isConnected,
    lastSyncLabel:
      typeof v.lastSyncLabel === "string" ? v.lastSyncLabel : DEFAULT_WHATSAPP.lastSyncLabel,
  }
}

export function WhatsAppSettings() {
  const [settings, setSettings] = useState(DEFAULT_WHATSAPP)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isGeneratingQR, setIsGeneratingQR] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const rows = await fetchSettings("whatsapp")
        const row = rows.find((r) => r.key === "panel_whatsapp")
        if (!cancelled && row?.value) {
          setSettings(mergeWhatsappValue(row.value))
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

  const persist = async (next: typeof DEFAULT_WHATSAPP) => {
    await updateSetting("panel_whatsapp", next as unknown as Record<string, unknown>)
  }

  const handleDisconnect = async () => {
    const next = { ...settings, isConnected: false }
    setSettings(next)
    try {
      await persist(next)
      toast.success("Estado salvo: desconectado")
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao salvar")
    }
  }

  const handleGenerateQR = () => {
    setIsGeneratingQR(true)
    setTimeout(() => {
      setIsGeneratingQR(false)
      toast.info(
        "A vinculação por QR depende do serviço WhatsApp no backend; configure o provedor correspondente.",
      )
    }, 1200)
  }

  const handleSave = async () => {
    try {
      await persist(settings)
      toast.success("Configurações do WhatsApp salvas")
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao salvar")
    }
  }

  return (
    <div className="space-y-6">
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground font-heading">
            Status da Conexão
          </CardTitle>
          <CardDescription>
            Gerencie a conexão do WhatsApp Business
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <p className="text-sm text-destructive border border-destructive/30 rounded-md p-2 mb-4">
              {error}
            </p>
          )}
          {loading ? (
            <Skeleton className="h-28 w-full rounded-lg" />
          ) : (
            <>
              <div className="space-y-4 mb-4">
                <div className="space-y-2">
                  <Label htmlFor="wa-phone">Número exibido</Label>
                  <Input
                    id="wa-phone"
                    value={settings.phone}
                    onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
                    placeholder="(00) 00000-0000"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="wa-sync">Última sincronização (texto)</Label>
                  <Input
                    id="wa-sync"
                    value={settings.lastSyncLabel}
                    onChange={(e) => setSettings({ ...settings, lastSyncLabel: e.target.value })}
                    placeholder="ex.: há 5 minutos"
                  />
                </div>
                <div className="flex items-center justify-between rounded-lg border border-border p-3">
                  <Label htmlFor="wa-connected" className="cursor-pointer">
                    Exibir como conectado
                  </Label>
                  <Switch
                    id="wa-connected"
                    checked={settings.isConnected}
                    onCheckedChange={(checked) => setSettings({ ...settings, isConnected: checked })}
                  />
                </div>
              </div>
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10">
                    <Smartphone className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{settings.phone}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {settings.isConnected ? (
                        <>
                          <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                          </span>
                          <span className="text-sm text-primary font-medium">Conectado</span>
                        </>
                      ) : (
                        <>
                          <span className="h-2 w-2 rounded-full bg-muted-foreground"></span>
                          <span className="text-sm text-muted-foreground">Desconectado</span>
                        </>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Última sincronização: {settings.lastSyncLabel}
                    </p>
                  </div>
                </div>
                {settings.isConnected && (
                  <Button
                    variant="outline"
                    onClick={() => void handleDisconnect()}
                    className="border-destructive text-destructive hover:bg-destructive/10"
                  >
                    Desconectar
                  </Button>
                )}
              </div>
              <Button onClick={() => void handleSave()} className="w-full mt-4 bg-primary hover:bg-primary/90">
                Salvar alterações
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground font-heading">
            Conectar Novo Dispositivo
          </CardTitle>
          <CardDescription>
            Escaneie o QR Code para vincular um número do WhatsApp
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <Skeleton className="h-64 w-full rounded-lg" />
          ) : (
            <>
              <div className="flex flex-col items-center p-6 bg-muted/30 rounded-lg">
                <div className="w-48 h-48 bg-muted rounded-lg flex items-center justify-center mb-4">
                  {isGeneratingQR ? (
                    <RefreshCw className="h-8 w-8 text-muted-foreground animate-spin" />
                  ) : (
                    <QrCode className="h-16 w-16 text-muted-foreground" />
                  )}
                </div>
                <Button
                  onClick={handleGenerateQR}
                  disabled={isGeneratingQR}
                  className="bg-primary hover:bg-primary/90"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isGeneratingQR ? "animate-spin" : ""}`} />
                  {isGeneratingQR ? "Gerando..." : "Gerar novo QR Code"}
                </Button>
              </div>

              <div className="p-4 bg-secondary/10 rounded-lg">
                <p className="text-sm font-medium text-foreground mb-2">
                  Como conectar:
                </p>
                <ol className="text-sm text-muted-foreground space-y-1.5 list-decimal list-inside">
                  <li>Abra o WhatsApp no seu celular</li>
                  <li>{"Toque em Menu > Dispositivos conectados"}</li>
                  <li>Toque em Conectar dispositivo</li>
                  <li>Escaneie o QR Code acima</li>
                </ol>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
