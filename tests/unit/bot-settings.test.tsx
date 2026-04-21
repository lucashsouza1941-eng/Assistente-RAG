import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { BotSettings } from "@/components/settings/bot-settings"

const toastSuccess = vi.fn()
const toastError = vi.fn()

vi.mock("sonner", () => ({
  toast: {
    success: (...a: unknown[]) => toastSuccess(...a),
    error: (...a: unknown[]) => toastError(...a),
  },
}))

const fetchSettings = vi.fn()
const updateSetting = vi.fn()

vi.mock("@/lib/api-client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("@/lib/api-client")>()
  return {
    ...mod,
    fetchSettings: (...a: unknown[]) => fetchSettings(...a),
    updateSetting: (...a: unknown[]) => updateSetting(...a),
  }
})

describe("BotSettings", () => {
  beforeEach(() => {
    toastSuccess.mockReset()
    toastError.mockReset()
    fetchSettings.mockReset()
    updateSetting.mockReset()
    fetchSettings.mockResolvedValue([
      { id: 1, key: "bot.clinic_name", value: { v: "Clínica Teste" }, category: "bot" },
      { id: 2, key: "bot.welcome_message", value: { v: "Olá!" }, category: "bot" },
      { id: 3, key: "bot.closing_message", value: { v: "Tchau!" }, category: "bot" },
      { id: 4, key: "bot.respond_outside_hours", value: { v: false }, category: "bot" },
      { id: 5, key: "bot.business_hours_start", value: { v: "08:00" }, category: "bot" },
      { id: 6, key: "bot.business_hours_end", value: { v: "18:00" }, category: "bot" },
      {
        id: 7,
        key: "bot.work_days",
        value: { v: { seg: true, ter: true, qua: true, qui: true, sex: true, sab: false, dom: false } },
        category: "bot",
      },
    ])
    updateSetting.mockResolvedValue({ id: 1, key: "bot.clinic_name", value: { v: "x" }, category: "bot" })
  })

  it("carrega dados da API e mostra o nome do assistente", async () => {
    render(<BotSettings />)

    await waitFor(() => {
      expect(screen.getByLabelText(/nome do assistente/i)).toHaveValue("Clínica Teste")
    })

    expect(fetchSettings).toHaveBeenCalledWith("bot")
  })

  it("salva alterações e chama updateSetting para cada chave", async () => {
    const user = userEvent.setup()
    render(<BotSettings />)

    await waitFor(() => {
      expect(screen.getByLabelText(/nome do assistente/i)).toBeInTheDocument()
    })

    const nameInput = screen.getByLabelText(/nome do assistente/i)
    fireEvent.change(nameInput, { target: { value: "Novo Nome" } })

    await user.click(screen.getByRole("button", { name: /salvar configurações/i }))

    await waitFor(() => {
      expect(toastSuccess).toHaveBeenCalledWith("Configurações do bot salvas")
    })

    expect(updateSetting).toHaveBeenCalled()
    expect(updateSetting.mock.calls.some((c) => c[0] === "bot.clinic_name")).toBe(true)
  })
})
