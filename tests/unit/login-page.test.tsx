import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import LoginPage from "@/app/login/page"

const signIn = vi.fn()

vi.mock("next-auth/react", () => ({
  signIn: (...args: unknown[]) => signIn(...args),
}))

describe("LoginPage", () => {
  beforeEach(() => {
    signIn.mockReset()
  })

  it("submete a senha e chama signIn com credentials", async () => {
    signIn.mockResolvedValue({ ok: true, error: null, status: 200, url: "/" })

    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText(/senha/i), "minha-senha-segura")
    await user.click(screen.getByRole("button", { name: /^entrar$/i }))

    expect(signIn).toHaveBeenCalledWith(
      "credentials",
      expect.objectContaining({
        password: "minha-senha-segura",
        redirect: false,
        callbackUrl: "/",
      }),
    )
  })

  it("mostra mensagem quando a senha está incorreta", async () => {
    signIn.mockResolvedValue({ ok: false, error: "CredentialsSignin", status: 401, url: null })

    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText(/senha/i), "errada")
    await user.click(screen.getByRole("button", { name: /^entrar$/i }))

    expect(screen.getByText(/senha incorreta/i)).toBeInTheDocument()
  })
})
