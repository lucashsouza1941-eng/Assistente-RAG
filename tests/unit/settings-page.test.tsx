import type { ReactNode } from "react"
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import SettingsPage from "@/app/settings/page"

vi.mock("@/components/admin-layout", () => ({
  AdminLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="admin-layout">{children}</div>
  ),
}))

vi.mock("@/components/settings/bot-settings", () => ({
  BotSettings: () => <div data-testid="panel-bot">Conteúdo Bot</div>,
}))

vi.mock("@/components/settings/ai-settings", () => ({
  AISettings: () => <div data-testid="panel-ai">Conteúdo IA</div>,
}))

vi.mock("@/components/settings/whatsapp-settings", () => ({
  WhatsAppSettings: () => <div data-testid="panel-whatsapp">Conteúdo WhatsApp</div>,
}))

vi.mock("@/components/settings/notification-settings", () => ({
  NotificationSettings: () => <div data-testid="panel-notifications">Conteúdo Notificações</div>,
}))

describe("SettingsPage (painel de configurações)", () => {
  it("renderiza o título e as abas principais", () => {
    render(<SettingsPage />)

    expect(screen.getByRole("heading", { name: /configurações/i })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: /^bot$/i })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: /^ia$/i })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: /^whatsapp$/i })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: /notificações/i })).toBeInTheDocument()
  })

  it("mostra o painel Bot por defeito", () => {
    render(<SettingsPage />)
    expect(screen.getByTestId("panel-bot")).toBeVisible()
    // Radix Tabs não mantém o conteúdo das abas inativas montado no DOM
    expect(screen.queryByTestId("panel-ai")).not.toBeInTheDocument()
  })

  it("alterna para o painel IA ao clicar no separador", async () => {
    const user = userEvent.setup()
    render(<SettingsPage />)

    await user.click(screen.getByRole("tab", { name: /^ia$/i }))

    expect(screen.getByTestId("panel-ai")).toBeVisible()
    expect(screen.queryByTestId("panel-bot")).not.toBeInTheDocument()
  })

  it("alterna para WhatsApp e Notificações", async () => {
    const user = userEvent.setup()
    render(<SettingsPage />)

    await user.click(screen.getByRole("tab", { name: /^whatsapp$/i }))
    expect(screen.getByTestId("panel-whatsapp")).toBeVisible()

    await user.click(screen.getByRole("tab", { name: /notificações/i }))
    expect(screen.getByTestId("panel-notifications")).toBeVisible()
  })
})
