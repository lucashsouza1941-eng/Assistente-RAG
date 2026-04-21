import { describe, it, expect, vi, beforeEach } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { FileUpload } from "@/components/knowledge/file-upload"

const toastError = vi.fn()
const toastSuccess = vi.fn()
const uploadDocument = vi.fn()

vi.mock("sonner", () => ({
  toast: {
    error: (...a: unknown[]) => toastError(...a),
    success: (...a: unknown[]) => toastSuccess(...a),
  },
}))

vi.mock("@/lib/api-client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("@/lib/api-client")>()
  return {
    ...mod,
    uploadDocument: (...a: unknown[]) => uploadDocument(...a),
  }
})

describe("FileUpload", () => {
  beforeEach(() => {
    toastError.mockReset()
    toastSuccess.mockReset()
    uploadDocument.mockReset()
    uploadDocument.mockResolvedValue(undefined)
  })

  it("aceita PDF e mostra o ficheiro na fila de envio", async () => {
    const user = userEvent.setup()
    const { container } = render(<FileUpload />)

    const input = container.querySelector("#file-upload") as HTMLInputElement
    expect(input).toBeTruthy()

    const file = new File(["%PDF-1.4"], "doc.pdf", { type: "application/pdf" })
    await user.upload(input, file)

    expect(screen.getByText("doc.pdf")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /enviar 1 arquivo/i })).toBeInTheDocument()
  })

  it("rejeita extensão inválida e chama toast.error", () => {
    render(<FileUpload />)

    const dropZone = screen.getByText(/Arraste arquivos ou clique para selecionar/i).closest("label")!
      .parentElement!
    const file = new File(["x"], "hack.exe", { type: "application/octet-stream" })
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] } as unknown as DataTransfer,
    })

    expect(toastError).toHaveBeenCalled()
    expect(screen.queryByText("hack.exe")).not.toBeInTheDocument()
  })

  it("envia ficheiros pendentes e chama uploadDocument", async () => {
    const user = userEvent.setup()
    const onUploaded = vi.fn()
    const { container } = render(<FileUpload onUploaded={onUploaded} />)

    const input = container.querySelector("#file-upload") as HTMLInputElement
    await user.upload(input, new File(["x"], "a.pdf", { type: "application/pdf" }))

    await user.click(screen.getByRole("button", { name: /enviar 1 arquivo/i }))

    expect(uploadDocument).toHaveBeenCalledTimes(1)
    expect(uploadDocument).toHaveBeenCalledWith(
      expect.any(File),
      "a",
      "GENERAL",
    )
    expect(toastSuccess).toHaveBeenCalled()
    expect(onUploaded).toHaveBeenCalled()
  })

  it("mostra título e instruções de arrastar ficheiros", () => {
    render(<FileUpload />)
    expect(screen.getByText(/upload de documentos/i)).toBeInTheDocument()
    expect(screen.getByText(/arraste arquivos ou clique para selecionar/i)).toBeInTheDocument()
    expect(screen.getByText(/pdf, txt, docx/i)).toBeInTheDocument()
  })
})
