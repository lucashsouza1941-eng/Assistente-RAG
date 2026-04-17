"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Smartphone, RefreshCw, Copy, ExternalLink } from "lucide-react"
import { useState, useEffect, useCallback } from "react"
import { toast } from "sonner"
import {
  ApiRequestError,
  fetchSettings,
  fetchWhatsAppConnection,
  putWhatsAppCredentials,
  type WhatsAppConnectionStatus,
} from "@/lib/api-client"
import { Skeleton } from "@/components/ui/skeleton"
import { indexByKey, putScalarKey, unwrapSettingValue } from "@/lib/settings-values"

const DEFAULT_DISPLAY = {
  phone: "",
  lastSyncLabel: "",
}

function loadDisplayFromRows(rows: ReturnType<typeof indexByKey>) {
  const legacy = rows.get("panel_whatsapp")
  if (legacy) {
    const u = unwrapSettingValue(legacy)
    if (u && typeof u === "object") {
      const o = u as Record<string, unknown>
      return {
        phone: typeof o.phone === "string" ? o.phone : "",
        lastSyncLabel: typeof o.lastSyncLabel === "string" ? o.lastSyncLabel : "",
      }
    }
  }
  const phone = unwrapSettingValue(rows.get("whatsapp.display_phone"))
  const sync = unwrapSettingValue(rows.get("whatsapp.last_sync_label"))
  return {
    phone: typeof phone === "string" ? phone : "",
    lastSyncLabel: typeof sync === "string" ? sync : "",
  }
}

export function WhatsAppSettings() {
  const [display, setDisplay] = useState(DEFAULT_DISPLAY)
  const [connection, setConnection] = useState<WhatsAppConnectionStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [phoneNumberId, setPhoneNumberId] = useState("")
  const [accessToken, setAccessToken] = useState("")
  const [verifyToken, setVerifyToken] = useState("")
  const [savingCreds, setSavingCreds] = useState(false)

  const loadConnection = useCallback(async () => {
    setRefreshing(true)
    setError(null)
    try {
      const status = await fetchWhatsAppConnection()
      setConnection(status)
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Erro ao consultar Meta API")
      setConnection(null)
    } finally {
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const rowsList = await fetchSettings("whatsapp")
        const rows = indexByKey(rowsList)
        if (!cancelled) setDisplay(loadDisplayFromRows(rows))
        try {
          const st = await fetchWhatsAppConnection()
          if (!cancelled) setConnection(st)
        } catch (e) {
          if (!cancelled) {
            setError(e instanceof ApiRequestError ? e.message : "Erro ao consultar Meta API")
            setConnection(null)
          }
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

  const handleRefreshStatus = () => {
    void loadConnection()
  }

  const persistDisplay = async () => {
    await Promise.all([
      putScalarKey("whatsapp.display_phone", display.phone),
      putScalarKey("whatsapp.last_sync_label", display.lastSyncLabel),
      putScalarKey("whatsapp.display_connected", Boolean(connection?.connected)),
    ])
  }

  const handleSaveDisplay = async () => {
    try {
      await persistDisplay()
      toast.success("Preferências de exibição salvas")
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao salvar")
    }
  }

  const handleSaveCredentials = async () => {
    setSavingCreds(true)
    try {
      const body: { phone_number_id?: string; access_token?: string; verify_token?: string } = {}
      if (phoneNumberId.trim()) body.phone_number_id = phoneNumberId.trim()
      if (accessToken.trim()) body.access_token = accessToken.trim()
      if (verifyToken.trim()) body.verify_token = verifyToken.trim()
      if (Object.keys(body).length === 0) {
        toast.info("Preencha ao menos um campo para atualizar.")
        return
      }
      await putWhatsAppCredentials(body)
      setPhoneNumberId("")
      setAccessToken("")
      setVerifyToken("")
      toast.success("Credenciais gravadas na base. Reinicie a API se também usar variáveis de ambiente.")
      await loadConnection()
    } catch (e) {
      toast.error(e instanceof ApiRequestError ? e.message : "Falha ao salvar credenciais")
    } finally {
      setSavingCreds(false)
    }
  }

  const copyWebhook = () => {
    const url = connection?.public_webhook_url
    if (!url) {
      toast.error("Defina PUBLIC_API_BASE_URL no servidor para exibir a URL do webhook.")
      return
    }
    void navigator.clipboard.writeText(url)
    toast.success("URL copiada")
  }

  return (
    <div className="space-y-6">
      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base font-semibold text-foreground font-heading">
              WhatsApp Cloud API — status
            </CardTitle>
            <CardDescription>
              Verificação em tempo real via Graph API (credenciais do servidor ou gravadas abaixo).
            </CardDescription>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void handleRefreshStatus()}
            disabled={refreshing || loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Atualizar status
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="text-sm text-destructive border border-destructive/30 rounded-md p-2">{error}</p>
          )}
          {loading ? (
            <Skeleton className="h-32 w-full rounded-lg" />
          ) : connection ? (
            <>
              <div className="flex items-start gap-4 p-4 bg-muted/50 rounded-lg">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 shrink-0">
                  <Smartphone className="h-6 w-6 text-primary" />
                </div>
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`text-sm font-medium ${connection.connected ? "text-primary" : "text-destructive"}`}
                    >
                      {connection.connected ? "Conectado à Meta" : "Falha na verificação"}
                    </span>
                  </div>
                  {connection.display_phone_number && (
                    <p className="text-sm font-medium text-foreground">
                      {connection.display_phone_number}
                    </p>
                  )}
                  {connection.verified_name && (
                    <p className="text-xs text-muted-foreground">Verificado: {connection.verified_name}</p>
                  )}
                  <p className="text-xs text-muted-foreground font-mono break-all">
                    Phone number ID: {connection.phone_number_id}
                  </p>
                  {connection.error && (
                    <p className="text-xs text-destructive mt-2">{connection.error}</p>
                  )}
                  <div className="flex flex-wrap gap-3 text-xs text-muted-foreground pt-2">
                    <span>Token API: {connection.access_token_configured ? "configurado" : "ausente"}</span>
                    <span>Verify token: {connection.verify_token_configured ? "configurado" : "ausente"}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>URL do webhook (callback)</Label>
                <div className="flex gap-2 flex-wrap">
                  <Input
                    readOnly
                    value={connection.public_webhook_url || "(defina PUBLIC_API_BASE_URL na API)"}
                    className="font-mono text-xs flex-1 min-w-[200px]"
                  />
                  <Button type="button" variant="outline" size="icon" onClick={copyWebhook} title="Copiar">
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  No Meta for Developers → WhatsApp → Configuration, use esta URL e o mesmo verify token salvo
                  aqui ou em WHATSAPP_VERIFY_TOKEN.
                </p>
                <a
                  href="https://developers.facebook.com/docs/whatsapp/cloud-api/get-started"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-xs text-primary hover:underline"
                >
                  Documentação Cloud API <ExternalLink className="h-3 w-3 ml-1" />
                </a>
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground font-heading">
            Credenciais (persistidas na base)
          </CardTitle>
          <CardDescription>
            Opcional: sobrescrevem WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN e WHATSAPP_VERIFY_TOKEN
            para este ambiente. Deixe em branco para não alterar.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="wa-pnid">Phone Number ID</Label>
            <Input
              id="wa-pnid"
              value={phoneNumberId}
              onChange={(e) => setPhoneNumberId(e.target.value)}
              placeholder="ID do número no Graph API"
              autoComplete="off"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="wa-token">Access token (long-lived)</Label>
            <Input
              id="wa-token"
              type="password"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              placeholder="EAA..."
              autoComplete="off"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="wa-verify">Verify token (webhook GET)</Label>
            <Input
              id="wa-verify"
              type="password"
              value={verifyToken}
              onChange={(e) => setVerifyToken(e.target.value)}
              placeholder="Mesmo valor configurado no painel Meta"
              autoComplete="off"
            />
          </div>
          <Button
            type="button"
            onClick={() => void handleSaveCredentials()}
            disabled={savingCreds}
            className="w-full bg-primary hover:bg-primary/90"
          >
            {savingCreds ? "Salvando…" : "Salvar credenciais"}
          </Button>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground font-heading">
            Exibição no painel
          </CardTitle>
          <CardDescription>Rótulos locais (não alteram a API Meta).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <Skeleton className="h-24 w-full" />
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="wa-phone">Texto do número (exibição)</Label>
                <Input
                  id="wa-phone"
                  value={display.phone}
                  onChange={(e) => setDisplay({ ...display, phone: e.target.value })}
                  placeholder="(00) 00000-0000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="wa-sync">Nota / última verificação (texto livre)</Label>
                <Input
                  id="wa-sync"
                  value={display.lastSyncLabel}
                  onChange={(e) => setDisplay({ ...display, lastSyncLabel: e.target.value })}
                  placeholder="ex.: verificado agora"
                />
              </div>
              <Button type="button" onClick={() => void handleSaveDisplay()} className="w-full">
                Salvar exibição
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
