import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ContactForm } from "@/components/landing/ContactForm";

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    form: ({ children, ...props }: any) => <form {...props}>{children}</form>,
  },
}));

// Mock fetch
global.fetch = jest.fn();

// Mock reCAPTCHA
(global as any).grecaptcha = {
  ready: (callback: () => void) => callback(),
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

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

describe("ContactForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ message: "Success" }),
    });
  });

  it("renders form heading", () => {
    render(<ContactForm />);

    const heading = screen.getByRole("heading", { name: /Получите бесплатную консультацию/i });
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

    const consent = screen.getByText(/Я согласен на обработку персональных данных/i);
    expect(consent).toBeInTheDocument();
    expect(screen.getByText(/ФЗ-152/i)).toBeInTheDocument();
  });

  it("shows validation errors for empty required fields", async () => {
    render(<ContactForm />);

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Имя должно содержать минимум 2 символа/i)).toBeInTheDocument();
      expect(screen.getByText(/Введите корректный номер телефона/i)).toBeInTheDocument();
      expect(screen.getByText(/Введите корректный email адрес/i)).toBeInTheDocument();
    });
  });

  it("validates phone number format", async () => {
    render(<ContactForm />);

    const phoneInput = screen.getByLabelText(/Телефон/i);
    fireEvent.change(phoneInput, { target: { value: "123" } });
    fireEvent.blur(phoneInput);

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Введите корректный номер телефона/i)).toBeInTheDocument();
    });
  });

  it("validates email format", async () => {
    render(<ContactForm />);

    const emailInput = screen.getByLabelText(/Email/i);
    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.blur(emailInput);

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Введите корректный email адрес/i)).toBeInTheDocument();
    });
  });

  it("requires FZ-152 consent", async () => {
    render(<ContactForm />);

    // Fill all fields except consent
    fireEvent.change(screen.getByLabelText(/Ваше имя/i), { target: { value: "Иван Иванов" } });
    fireEvent.change(screen.getByLabelText(/Телефон/i), { target: { value: "+7 999 123-45-67" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "ivan@example.com" } });
    fireEvent.change(screen.getByLabelText(/Название клиники/i), { target: { value: "Клиника" } });
    fireEvent.change(screen.getByLabelText(/Специализация/i), { target: { value: "dentistry" } });

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Необходимо согласие на обработку персональных данных/i)).toBeInTheDocument();
    });
  });

  it("submits form with valid data", async () => {
    render(<ContactForm />);

    // Fill all fields
    fireEvent.change(screen.getByLabelText(/Ваше имя/i), { target: { value: "Иван Иванов" } });
    fireEvent.change(screen.getByLabelText(/Телефон/i), { target: { value: "+7 999 123-45-67" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "ivan@example.com" } });
    fireEvent.change(screen.getByLabelText(/Название клиники/i), { target: { value: "Клиника Здоровье" } });
    fireEvent.change(screen.getByLabelText(/Специализация/i), { target: { value: "dentistry" } });
    fireEvent.change(screen.getByLabelText(/Сообщение/i), { target: { value: "Хочу увеличить поток пациентов" } });

    const consentCheckbox = screen.getByRole("checkbox");
    fireEvent.click(consentCheckbox);

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
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

  it("shows success message after submission", async () => {
    render(<ContactForm />);

    // Fill and submit form
    fireEvent.change(screen.getByLabelText(/Ваше имя/i), { target: { value: "Иван Иванов" } });
    fireEvent.change(screen.getByLabelText(/Телефон/i), { target: { value: "+7 999 123-45-67" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "ivan@example.com" } });
    fireEvent.change(screen.getByLabelText(/Название клиники/i), { target: { value: "Клиника" } });
    fireEvent.change(screen.getByLabelText(/Специализация/i), { target: { value: "dentistry" } });
    fireEvent.click(screen.getByRole("checkbox"));

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Спасибо за обращение!/i)).toBeInTheDocument();
      expect(screen.getByText(/Мы получили вашу заявку/i)).toBeInTheDocument();
    });
  });

  it("shows error message on submission failure", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ message: "Server error" }),
    });

    render(<ContactForm />);

    // Fill and submit form
    fireEvent.change(screen.getByLabelText(/Ваше имя/i), { target: { value: "Иван Иванов" } });
    fireEvent.change(screen.getByLabelText(/Телефон/i), { target: { value: "+7 999 123-45-67" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "ivan@example.com" } });
    fireEvent.change(screen.getByLabelText(/Название клиники/i), { target: { value: "Клиника" } });
    fireEvent.change(screen.getByLabelText(/Специализация/i), { target: { value: "dentistry" } });
    fireEvent.click(screen.getByRole("checkbox"));

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Server error/i)).toBeInTheDocument();
    });
  });

  it("disables submit button during submission", async () => {
    render(<ContactForm />);

    // Fill form
    fireEvent.change(screen.getByLabelText(/Ваше имя/i), { target: { value: "Иван Иванов" } });
    fireEvent.change(screen.getByLabelText(/Телефон/i), { target: { value: "+7 999 123-45-67" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "ivan@example.com" } });
    fireEvent.change(screen.getByLabelText(/Название клиники/i), { target: { value: "Клиника" } });
    fireEvent.change(screen.getByLabelText(/Специализация/i), { target: { value: "dentistry" } });
    fireEvent.click(screen.getByRole("checkbox"));

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
    fireEvent.click(submitButton);

    expect(submitButton).toBeDisabled();
  });

  it("saves draft to localStorage", async () => {
    render(<ContactForm />);

    fireEvent.change(screen.getByLabelText(/Ваше имя/i), { target: { value: "Иван" } });

    await waitFor(() => {
      const draft = localStorageMock.getItem("aim_contact_form_draft");
      expect(draft).toBeTruthy();
      const parsed = JSON.parse(draft!);
      expect(parsed.data.name).toBe("Иван");
    });
  });

  it("loads draft from localStorage on mount", () => {
    const draft = {
      data: {
        name: "Иван Иванов",
        phone: "+7 999 123-45-67",
        email: "ivan@example.com",
      },
      timestamp: Date.now(),
    };
    localStorageMock.setItem("aim_contact_form_draft", JSON.stringify(draft));

    render(<ContactForm />);

    expect(screen.getByLabelText(/Ваше имя/i)).toHaveValue("Иван Иванов");
    expect(screen.getByLabelText(/Телефон/i)).toHaveValue("+7 999 123-45-67");
    expect(screen.getByLabelText(/Email/i)).toHaveValue("ivan@example.com");
  });

  it("clears draft after successful submission", async () => {
    render(<ContactForm />);

    // Fill and submit
    fireEvent.change(screen.getByLabelText(/Ваше имя/i), { target: { value: "Иван Иванов" } });
    fireEvent.change(screen.getByLabelText(/Телефон/i), { target: { value: "+7 999 123-45-67" } });
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "ivan@example.com" } });
    fireEvent.change(screen.getByLabelText(/Название клиники/i), { target: { value: "Клиника" } });
    fireEvent.change(screen.getByLabelText(/Специализация/i), { target: { value: "dentistry" } });
    fireEvent.click(screen.getByRole("checkbox"));

    const submitButton = screen.getByRole("button", { name: /Получить консультацию/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(localStorageMock.getItem("aim_contact_form_draft")).toBeNull();
    });
  });

  it("renders reCAPTCHA notice", () => {
    render(<ContactForm />);

    expect(screen.getByText(/Этот сайт защищён reCAPTCHA/i)).toBeInTheDocument();
  });

  it("has proper ARIA labels", () => {
    render(<ContactForm />);

    const section = screen.getByRole("region", { name: "Получите бесплатную консультацию" });
    expect(section).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<ContactForm className="custom-class" />);

    const section = container.querySelector("section");
    expect(section).toHaveClass("custom-class");
  });
});
