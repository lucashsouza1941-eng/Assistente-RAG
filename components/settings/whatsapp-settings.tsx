"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Smartphone, QrCode, RefreshCw } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

export function WhatsAppSettings() {
  const [isConnected, setIsConnected] = useState(true)
  const [isGeneratingQR, setIsGeneratingQR] = useState(false)

  const handleDisconnect = () => {
    setIsConnected(false)
    toast.success("WhatsApp desconectado")
  }

  const handleGenerateQR = () => {
    setIsGeneratingQR(true)
    setTimeout(() => {
      setIsGeneratingQR(false)
      toast.success("QR Code gerado! Escaneie com seu WhatsApp")
    }, 2000)
  }

  return (
    <div className="space-y-6">
      {/* Connection Status Card */}
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
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10">
                <Smartphone className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-medium text-foreground">(11) 98765-4321</p>
                <div className="flex items-center gap-2 mt-1">
                  {isConnected ? (
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
                  Última sincronização: há 5 minutos
                </p>
              </div>
            </div>
            {isConnected && (
              <Button
                variant="outline"
                onClick={handleDisconnect}
                className="border-destructive text-destructive hover:bg-destructive/10"
              >
                Desconectar
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* QR Code Card */}
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
        </CardContent>
      </Card>
    </div>
  )
}
