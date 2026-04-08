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
import { useState } from "react"
import { toast } from "sonner"

export function AISettings() {
  const [settings, setSettings] = useState({
    model: "gpt-4o",
    temperature: 0.3,
    maxTokens: 500,
    confidenceThreshold: 70,
  })

  const handleSave = () => {
    toast.success("Configurações de IA salvas com sucesso!")
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
            onChange={(e) => setSettings({ ...settings, maxTokens: parseInt(e.target.value) || 0 })}
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

        <Button onClick={handleSave} className="w-full bg-primary hover:bg-primary/90">
          Salvar Configurações
        </Button>
      </CardContent>
    </Card>
  )
}
