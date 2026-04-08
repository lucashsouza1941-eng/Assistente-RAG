"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { useState } from "react"
import { toast } from "sonner"

export function BotSettings() {
  const [settings, setSettings] = useState({
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
  })

  const handleSave = () => {
    toast.success("Configurações do bot salvas com sucesso!")
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

        <Button onClick={handleSave} className="w-full bg-primary hover:bg-primary/90">
          Salvar Configurações
        </Button>
      </CardContent>
    </Card>
  )
}
