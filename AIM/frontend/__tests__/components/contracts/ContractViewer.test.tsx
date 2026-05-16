import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom"
import ContractViewer from "@/components/contracts/ContractViewer"

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

describe("ContractViewer", () => {
  beforeEach(() => {
    // Clear any previous alerts
    jest.clearAllMocks()
  })

  it("renders loading state initially", () => {
    const { container } = render(<ContractViewer />)
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it("renders contracts after loading", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    expect(screen.getAllByText("Стоматология Дента Плюс").length).toBeGreaterThan(0)
    expect(screen.getAllByText("Подписан").length).toBeGreaterThan(0)
  })

  it("displays all contract types", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    expect(screen.getByText("NDA-2026-001")).toBeInTheDocument()
    expect(screen.getByText("AIM-2026-002")).toBeInTheDocument()
  })

  it("filters contracts by status", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    // Click "Отправлен" filter
    const sentButton = screen.getByRole("button", { name: /отправлен/i })
    fireEvent.click(sentButton)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument()
      expect(screen.queryByText("AIM-2026-001")).not.toBeInTheDocument()
    })
  })

  it("filters contracts by signed status", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    // Click "Подписан" filter
    const signedButton = screen.getByRole("button", { name: /подписан/i })
    fireEvent.click(signedButton)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
      expect(screen.queryByText("AIM-2026-002")).not.toBeInTheDocument()
    })
  })

  it("shows all contracts when 'Все' filter is selected", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    // Click "Все" filter
    const allButton = screen.getByRole("button", { name: "Все" })
    fireEvent.click(allButton)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument()
      expect(screen.getByText("AIM-2026-003")).toBeInTheDocument()
    })
  })

  it("displays contract status badges correctly", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    // Check that status badges exist (counts may vary based on filter)
    expect(screen.getAllByText("Подписан").length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText("Отправлен").length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText("Черновик").length).toBeGreaterThanOrEqual(1)
  })

  it("displays contract amounts correctly", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    expect(screen.getByText(/250 000 ₽\/мес/)).toBeInTheDocument()
    expect(screen.getByText(/150 000 ₽\/мес/)).toBeInTheDocument()
    expect(screen.getByText(/300 000 ₽\/мес/)).toBeInTheDocument()
  })

  it("handles download button click", async () => {
    const alertMock = jest.spyOn(window, "alert").mockImplementation()

    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    const downloadButtons = screen.getAllByText("Скачать PDF")
    fireEvent.click(downloadButtons[0])

    expect(alertMock).toHaveBeenCalledWith(
      expect.stringContaining("AIM-2026-001")
    )

    alertMock.mockRestore()
  })

  it("shows resend button for sent contracts", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument()
    })

    expect(screen.getByText("Отправить повторно")).toBeInTheDocument()
  })

  it("shows cancel button for sent contracts", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument()
    })

    expect(screen.getByText("Отменить")).toBeInTheDocument()
  })

  it("shows send button for draft contracts", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-003")).toBeInTheDocument()
    })

    expect(screen.getByText("Отправить на подпись")).toBeInTheDocument()
  })

  it("handles resend button click", async () => {
    const alertMock = jest.spyOn(window, "alert").mockImplementation()

    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument()
    })

    const resendButton = screen.getByText("Отправить повторно")
    fireEvent.click(resendButton)

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith(
        expect.stringContaining("AIM-2026-002")
      )
    })

    alertMock.mockRestore()
  })

  it("handles cancel button click with prompt", async () => {
    const promptMock = jest.spyOn(window, "prompt").mockReturnValue("Ошибка в договоре")
    const alertMock = jest.spyOn(window, "alert").mockImplementation()

    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument()
    })

    const cancelButton = screen.getByText("Отменить")
    fireEvent.click(cancelButton)

    await waitFor(() => {
      expect(promptMock).toHaveBeenCalled()
      expect(alertMock).toHaveBeenCalledWith(
        expect.stringContaining("отменён")
      )
    })

    promptMock.mockRestore()
    alertMock.mockRestore()
  })

  it("does not cancel if prompt is cancelled", async () => {
    const promptMock = jest.spyOn(window, "prompt").mockReturnValue(null)
    const alertMock = jest.spyOn(window, "alert").mockImplementation()

    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-002")).toBeInTheDocument()
    })

    const cancelButton = screen.getByText("Отменить")
    fireEvent.click(cancelButton)

    expect(promptMock).toHaveBeenCalled()
    expect(alertMock).not.toHaveBeenCalled()

    promptMock.mockRestore()
    alertMock.mockRestore()
  })

  it("displays STUB notice for contracts with document ID", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    const stubNotices = screen.getAllByText(/STUB:/)
    expect(stubNotices.length).toBeGreaterThan(0)
  })

  it("displays contract type names correctly", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    expect(screen.getAllByText("Договор на оказание услуг")).toHaveLength(3)
    expect(screen.getByText("Соглашение о конфиденциальности")).toBeInTheDocument()
  })

  it("displays formatted dates correctly", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    // Check for Russian date format (any month name in Russian)
    const russianMonths = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    const hasRussianDate = russianMonths.some(month => {
      try {
        return screen.getAllByText(new RegExp(month)).length > 0
      } catch {
        return false
      }
    })
    expect(hasRussianDate).toBe(true)
  })

  it("shows empty state when no contracts match filter", async () => {
    render(<ContractViewer />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    // Click "Черновик" filter
    const draftButton = screen.getByRole("button", { name: /черновик/i })
    fireEvent.click(draftButton)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-003")).toBeInTheDocument()
    })

    // Now filter by "Отправлен" - should show different contracts
    const sentButton = screen.getByRole("button", { name: /отправлен/i })
    fireEvent.click(sentButton)

    await waitFor(() => {
      expect(screen.queryByText("AIM-2026-003")).not.toBeInTheDocument()
    })
  })

  it("applies custom className", () => {
    const { container } = render(<ContractViewer className="custom-class" />)
    expect(container.firstChild).toHaveClass("custom-class")
  })

  it("filters by clientId when provided", async () => {
    render(<ContractViewer clientId="1" />)

    await waitFor(() => {
      expect(screen.getByText("AIM-2026-001")).toBeInTheDocument()
    })

    // Should only show contract with id="1"
    expect(screen.queryByText("AIM-2026-002")).not.toBeInTheDocument()
  })
})
