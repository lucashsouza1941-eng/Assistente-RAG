"use client"

import { AdminLayout } from "@/components/admin-layout"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BotSettings } from "@/components/settings/bot-settings"
import { AISettings } from "@/components/settings/ai-settings"
import { WhatsAppSettings } from "@/components/settings/whatsapp-settings"
import { NotificationSettings } from "@/components/settings/notification-settings"

export default function SettingsPage() {
  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-foreground font-heading">
            Configurações
          </h2>
          <p className="text-sm text-muted-foreground">
            Personalize o comportamento do assistente virtual
          </p>
        </div>

        <Tabs defaultValue="bot" className="space-y-6">
          <TabsList className="bg-muted/50 p-1">
            <TabsTrigger value="bot">Bot</TabsTrigger>
            <TabsTrigger value="ai">IA</TabsTrigger>
            <TabsTrigger value="whatsapp">WhatsApp</TabsTrigger>
            <TabsTrigger value="notifications">Notificações</TabsTrigger>
          </TabsList>

          <TabsContent value="bot">
            <BotSettings />
          </TabsContent>

          <TabsContent value="ai">
            <AISettings />
          </TabsContent>

          <TabsContent value="whatsapp">
            <WhatsAppSettings />
          </TabsContent>

          <TabsContent value="notifications">
            <NotificationSettings />
          </TabsContent>
        </Tabs>
      </div>
    </AdminLayout>
  )
}
