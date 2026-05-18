import React from "react";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CookieConsent, useCookieConsent } from "@/components/CookieConsent";

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => React.createElement("div", props, children),
    button: ({ children, ...props }: any) => React.createElement("button", props, children),
  },
  AnimatePresence: ({ children }: any) => children,
}));

describe("CookieConsent", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders consent banner when no consent stored", () => {
    render(<CookieConsent />);
    act(() => jest.advanceTimersByTime(500));
    expect(screen.getByText(/cookie/i)).toBeInTheDocument();
  });

  it("does not render when consent already stored", () => {
    localStorage.setItem("aim_cookie_consent", JSON.stringify({
      necessary: true,
      analytics: true,
      marketing: false,
    }));
    render(<CookieConsent />);
    act(() => jest.advanceTimersByTime(500));
    expect(screen.queryByText(/cookie/i)).not.toBeInTheDocument();
  });

  it("accepts all cookies", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<CookieConsent />);
    act(() => jest.advanceTimersByTime(500));

    const acceptBtn = screen.getByRole("button", { name: "Принять все" });
    await user.click(acceptBtn);

    const stored = JSON.parse(localStorage.getItem("aim_cookie_consent")!);
    expect(stored.necessary).toBe(true);
    expect(stored.analytics).toBe(true);
    expect(stored.marketing).toBe(true);
  });

  it("dispatches aimConsentChanged event on accept", async () => {
    const handler = jest.fn();
    window.addEventListener("aimConsentChanged", handler);

    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<CookieConsent />);
    act(() => jest.advanceTimersByTime(500));

    const acceptBtn = screen.getByRole("button", { name: "Принять все" });
    await user.click(acceptBtn);

    expect(handler).toHaveBeenCalledTimes(1);
    window.removeEventListener("aimConsentChanged", handler);
  });

  it("allows partial consent (analytics off)", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<CookieConsent />);
    act(() => jest.advanceTimersByTime(500));

    // Аналитика включена по умолчанию — выключаем
    const analyticsToggle = screen.getByLabelText(/аналитика/i);
    await user.click(analyticsToggle);

    const acceptBtn = screen.getByRole("button", { name: "Принять выбранные" });
    await user.click(acceptBtn);

    const stored = JSON.parse(localStorage.getItem("aim_cookie_consent")!);
    expect(stored.necessary).toBe(true);
    expect(stored.analytics).toBe(false);
    expect(stored.marketing).toBe(false);
  });

  it("necessary cookies cannot be disabled", () => {
    render(<CookieConsent />);
    act(() => jest.advanceTimersByTime(500));
    const necessaryToggle = screen.getByLabelText(/необходимые/i) as HTMLInputElement;
    expect(necessaryToggle).toBeDisabled();
    expect(necessaryToggle).toBeChecked();
  });
});

describe("useCookieConsent", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns null when nothing stored", () => {
    let consent: any;
    function TestComponent() {
      consent = useCookieConsent();
      return null;
    }
    render(<TestComponent />);
    expect(consent).toBeNull();
  });

  it("returns stored consent preferences", () => {
    localStorage.setItem("aim_cookie_consent", JSON.stringify({
      necessary: true,
      analytics: true,
      marketing: true,
    }));

    let consent: any;
    function TestComponent() {
      consent = useCookieConsent();
      return null;
    }
    render(<TestComponent />);
    expect(consent.analytics).toBe(true);
    expect(consent.marketing).toBe(true);
  });
});
