import { test, expect, type Page } from "@playwright/test"

const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "admin123"

async function installCommonApiMocks(page: Page) {
  const conversations = [
    {
      id: "conv-1-critical",
      status: "ACTIVE",
      started_at: "2026-04-20T10:00:00.000Z",
    },
  ]
  const messages = [
    {
      id: "msg-user-1",
      role: "USER",
      content: "Oi, preciso de ajuda com um clareamento",
      created_at: "2026-04-20T10:02:00.000Z",
    },
    {
      id: "msg-bot-1",
      role: "ASSISTANT",
      content: "Claro! Posso explicar as opcoes de tratamento.",
      created_at: "2026-04-20T10:02:30.000Z",
    },
  ]

  await page.route("**/api/proxy/**", async (route) => {
    const req = route.request()
    const method = req.method()
    const url = new URL(req.url())
    const path = url.pathname

    if (method === "GET" && path.endsWith("/analytics/kpis")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total_conversations: 10,
          resolution_rate: 91,
          avg_response_time_ms: 650,
          patients_served: 8,
          escalation_rate: 4,
        }),
      })
    }

    if (method === "GET" && path.endsWith("/analytics/volume")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ timestamp: "10:00", count: 3 }]),
      })
    }

    if (method === "GET" && path.endsWith("/analytics/categories")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ category: "FAQ", count: 4, percentage: 40 }]),
      })
    }

    if (method === "GET" && path.endsWith("/knowledge/documents")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          size: 20,
          pages: 1,
        }),
      })
    }

    if (method === "POST" && path.endsWith("/knowledge/documents")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "doc-1",
          title: "guia-atendimento",
          type: "GENERAL",
          status: "INDEXED",
          chunks_count: 5,
          created_at: "2026-04-20T10:00:00.000Z",
        }),
      })
    }

    if (method === "GET" && path.endsWith("/settings/bot")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: 1, key: "bot.clinic_name", value: { v: "Clinica Teste" }, category: "bot" },
          { id: 2, key: "bot.welcome_message", value: { v: "Ola!" }, category: "bot" },
          { id: 3, key: "bot.closing_message", value: { v: "Ate logo!" }, category: "bot" },
          { id: 4, key: "bot.respond_outside_hours", value: { v: true }, category: "bot" },
          { id: 5, key: "bot.business_hours_start", value: { v: "08:00" }, category: "bot" },
          { id: 6, key: "bot.business_hours_end", value: { v: "18:00" }, category: "bot" },
          {
            id: 7,
            key: "bot.work_days",
            value: { v: { seg: true, ter: true, qua: true, qui: true, sex: true, sab: false, dom: false } },
            category: "bot",
          },
        ]),
      })
    }

    if (method === "PUT" && path.includes("/api/proxy/settings/")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 99,
          key: decodeURIComponent(path.split("/").pop() ?? "bot.unknown"),
          value: { v: "updated" },
          category: "bot",
        }),
      })
    }

    if (method === "GET" && path.endsWith("/chat/conversations")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: conversations,
          total: conversations.length,
          page: 1,
          size: 100,
          pages: 1,
        }),
      })
    }

    if (method === "GET" && /\/api\/proxy\/chat\/conversations\/[^/]+\/messages$/.test(path)) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(messages),
      })
    }

    if (method === "POST" && path.endsWith("/chat/message")) {
      const payload = req.postDataJSON() as { message?: string }
      messages.push({
        id: `msg-user-${messages.length + 1}`,
        role: "USER",
        content: payload.message ?? "mensagem",
        created_at: new Date().toISOString(),
      })
      messages.push({
        id: `msg-bot-${messages.length + 1}`,
        role: "ASSISTANT",
        content: "Resposta automatica recebida.",
        created_at: new Date().toISOString(),
      })
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          conversation_id: "conv-1-critical",
          response: "Resposta automatica recebida.",
          sources: [],
          latency_ms: 450,
          escalated: false,
        }),
      })
    }

    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: "{}",
    })
  })
}

async function login(page: Page) {
  await page.goto("/login")
  await page.getByLabel("Senha").fill(ADMIN_PASSWORD)
  await page.getByRole("button", { name: "Entrar" }).click()
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
}

test.describe("critical paths", () => {
  test.beforeEach(async ({ page }) => {
    await installCommonApiMocks(page)
  })

  test("1. login e logout completos", async ({ page }) => {
    await login(page)
    await page.getByRole("button", { name: "Sair" }).first().click()
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole("button", { name: "Entrar" })).toBeVisible()
  })

  test("2. upload de documento em Knowledge", async ({ page }) => {
    await login(page)
    await page.getByRole("link", { name: "Base de Conhecimento" }).click()
    await expect(page.getByRole("heading", { name: "Documentos indexados" })).toBeVisible()

    const fileInput = page.locator("#file-upload")
    await fileInput.setInputFiles({
      name: "guia-atendimento.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4 test file"),
    })

    await expect(page.getByText("guia-atendimento.pdf")).toBeVisible()
    await page.getByRole("button", { name: /Enviar 1 arquivo/i }).click()
    await expect(page.getByText("guia-atendimento.pdf")).not.toBeVisible()
  })

  test("3. alteracao e salvamento em Settings", async ({ page }) => {
    await login(page)
    await page.getByRole("link", { name: "Configurações" }).click()
    await expect(page.getByRole("heading", { name: "Configurações" })).toBeVisible()

    const assistantName = page.getByLabel("Nome do Assistente")
    await assistantName.fill("Assistente QA")
    await page.getByRole("button", { name: "Salvar Configurações" }).click()
    await expect(page.getByText("Configurações do bot salvas")).toBeVisible()
  })

  test("4. envio de mensagem no chat e recebimento de resposta", async ({ page }) => {
    await login(page)
    await page.getByRole("link", { name: "Conversas" }).click()
    await expect(page.getByRole("heading", { name: "Conversas" })).toBeVisible()
    await expect(page.getByText("Ref. conv-1-c…")).toBeVisible()

    await page.request.post("/api/proxy/chat/message", {
      data: {
        message: "Podem explicar opcoes de clareamento?",
        conversation_id: "conv-1-critical",
      },
    })

    await page.reload()
    await expect(page.getByText("Podem explicar opcoes de clareamento?")).toBeVisible()
    await expect(page.getByText("Resposta automatica recebida.")).toBeVisible()
  })
})
