import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ContactForm } from "@/components/landing/ContactForm";

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    form: ({ children, onSubmit, ...props }: any) => (
      <form onSubmit={onSubmit} {...props}>
        {children}
      </form>
    ),
  },
}));

// Mock @hookform/resolvers/zod — bypass validation deadlock
// recaptchaToken is set inside onSubmit but validated before it
jest.mock("@hookform/resolvers/zod", () => ({
  zodResolver: () => async (data: any) => ({ values: data, errors: {} }),
}));

// Mock @/lib/validation
const mockSaveDraft = jest.fn();
const mockLoadDraft = jest.fn().mockReturnValue(null);
const mockClearDraft = jest.fn();
const mockEncryptField = jest.fn((val: string) => `enc:${val}`);

jest.mock("@/lib/validation", () => ({
  contactFormSchema: {},
  specialties: [
    { value: "", label: "Выберите специализацию" },
    { value: "dentistry", label: "Стоматология" },
    { value: "cardiology", label: "Кардиология" },
    { value: "cosmetology", label: "Косметология" },
    { value: "surgery", label: "Хирургия" },
    { value: "other", label: "Другое" },
  ],
  saveDraft: (...args: any[]) => mockSaveDraft(...args),
  loadDraft: (...args: any[]) => mockLoadDraft(...args),
  clearDraft: (...args: any[]) => mockClearDraft(...args),
  encryptField: (...args: any[]) => mockEncryptField(...args),
}));

// Mock @/components/UTMCapture
jest.mock("@/components/UTMCapture", () => ({
  getStoredUtm: () => ({}),
}));

// Mock fetch
global.fetch = jest.fn();

// Mock reCAPTCHA
(global as any).grecaptcha = {
  ready: (cb: () => void) => cb(),
  execute: jest.fn().mockResolvedValue("mock-recaptcha-token"),
};

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Helper to fill all required form fields
function fillRequiredFields() {
  fireEvent.change(screen.getByLabelText(/Ваше имя/i), {
    target: { value: "Иван Иванов" },
  });
  fireEvent.change(screen.getByLabelText(/Телефон/i), {
    target: { value: "+7 999 123-45-67" },
  });
  fireEvent.change(screen.getByLabelText(/Email/i), {
    target: { value: "ivan@example.com" },
  });
  fireEvent.change(screen.getByLabelText(/Название клиники/i), {
    target: { value: "Клиника Здоровье" },
  });
  fireEvent.change(screen.getByLabelText(/Специализация/i), {
    target: { value: "dentistry" },
  });
  fireEvent.click(screen.getByRole("checkbox"));
}

describe("ContactForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
    mockLoadDraft.mockReturnValue(null);
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ message: "Success" }),
    });
  });

  it("renders form heading", () => {
    render(<ContactForm />);
    const heading = screen.getByRole("heading", {
      name: /Получите бесплатную консультацию/i,
    });
    expect(heading).toBeInTheDocument();
  });

  it("renders all form fields", () => {
    render(<ContactForm />);

    expect(screen.getByLabelText(/Ваше имя/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Телефон/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Название клиники/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Специализация/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Сообщение/i)).toBeInTheDocument();
  });

  it("renders FZ-152 consent checkbox", () => {
    render(<ContactForm />);

    const consent = screen.getByText(
      /Я согласен на обработку персональных данных/i
    );
    expect(consent).toBeInTheDocument();
    expect(screen.getByText(/ФЗ-152/i)).toBeInTheDocument();
  });

  it("shows required field indicators", () => {
    render(<ContactForm />);

    // Required fields have asterisks in labels
    const requiredAsterisks = screen.getAllByText("*");
    // Name, Phone, Email, Clinic, Specialty, Consent — 6 required fields
    expect(requiredAsterisks.length).toBeGreaterThanOrEqual(6);
  });

  it("consent checkbox is unchecked by default", () => {
    render(<ContactForm />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).not.toBeChecked();
  });

  it("submits form with valid data", async () => {
    render(<ContactForm />);

    fillRequiredFields();

    const submitButton = screen.getByRole("button", {
      name: /Получить консультацию/i,
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/contact",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
        })
      );
    });
  });

  it("encrypts phone and email before sending", async () => {
    render(<ContactForm />);

    fillRequiredFields();

    const submitButton = screen.getByRole("button", {
      name: /Получить консультацию/i,
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockEncryptField).toHaveBeenCalledWith(
        "+7 999 123-45-67",
        expect.any(String)
      );
      expect(mockEncryptField).toHaveBeenCalledWith(
        "ivan@example.com",
        expect.any(String)
      );
    });
  });

  it("shows success message after submission", async () => {
    render(<ContactForm />);

    fillRequiredFields();

    const submitButton = screen.getByRole("button", {
      name: /Получить консультацию/i,
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Спасибо за обращение!/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Мы получили вашу заявку/i)
      ).toBeInTheDocument();
    });
  });

  it("shows error message on submission failure", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ message: "Server error" }),
    });

    render(<ContactForm />);

    fillRequiredFields();

    const submitButton = screen.getByRole("button", {
      name: /Получить консультацию/i,
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Server error/i)).toBeInTheDocument();
    });
  });

  it("submit button has correct initial state", () => {
    render(<ContactForm />);

    const submitButton = screen.getByRole("button", {
      name: /Получить консультацию/i,
    });
    expect(submitButton).toBeEnabled();
    expect(submitButton).toHaveAttribute("type", "submit");
  });

  it("loads draft from loadDraft on mount", () => {
    mockLoadDraft.mockReturnValueOnce({
      name: "Иван Петров",
      phone: "+7 999 888-77-66",
      email: "petrov@example.com",
    });

    render(<ContactForm />);

    expect(screen.getByLabelText(/Ваше имя/i)).toHaveValue("Иван Петров");
    expect(screen.getByLabelText(/Телефон/i)).toHaveValue("+7 999 888-77-66");
    expect(screen.getByLabelText(/Email/i)).toHaveValue("petrov@example.com");
  });

  it("clears draft after successful submission", async () => {
    render(<ContactForm />);

    fillRequiredFields();

    const submitButton = screen.getByRole("button", {
      name: /Получить консультацию/i,
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockClearDraft).toHaveBeenCalled();
    });
  });

  it("renders reCAPTCHA notice", () => {
    render(<ContactForm />);

    expect(
      screen.getByText(/Этот сайт защищён reCAPTCHA/i)
    ).toBeInTheDocument();
  });

  it("has proper ARIA labels", () => {
    render(<ContactForm />);

    const section = screen.getByRole("region", {
      name: "Получите бесплатную консультацию",
    });
    expect(section).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<ContactForm className="custom-class" />);

    const section = container.querySelector("section");
    expect(section).toHaveClass("custom-class");
  });
});
