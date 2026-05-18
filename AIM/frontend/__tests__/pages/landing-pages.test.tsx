import React from "react";
import { render, screen } from "@testing-library/react";

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) =>
    React.createElement("a", { href, ...props }, children);
});

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

// Mock next/dynamic
jest.mock("next/dynamic", () => {
  return () => {
    const DynamicComponent = ({ children, ...props }: any) =>
      React.createElement("div", { "data-testid": "dynamic-component", ...props }, children);
    return DynamicComponent;
  };
});

// Mock framer-motion
const createMotionProxy = (tag: string) => {
  return ({ children, ...props }: any) => React.createElement(tag, props, children);
};

jest.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_target, prop: string) => {
        // Return a component for any HTML element name
        if (typeof prop === "string" && prop !== "$$typeof") {
          return createMotionProxy(prop);
        }
        return undefined;
      },
    }
  ),
  AnimatePresence: ({ children }: any) => children,
}));

// Mock react-hook-form
jest.mock("react-hook-form", () => ({
  useForm: () => ({
    register: (name: string) => ({ name }),
    handleSubmit: (fn: any) => (e: any) => { e?.preventDefault?.(); fn({}); },
    formState: { errors: {}, isDirty: false },
    watch: () => () => {},
    reset: () => {},
    setValue: () => {},
  }),
}));

// Suppress console errors from nested component rendering issues
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (typeof args[0] === "string" && args[0].includes("React")) return;
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

describe("Landing Pages", () => {
  it("renders home page without crashing", () => {
    const Home = require("@/app/page").default;
    render(<Home />);
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("renders privacy-policy page with ФЗ-152 content", async () => {
    const Page = require("@/app/privacy-policy/page").default;
    render(<Page />);
    // "политика" есть и в заголовке, и в тексте
    expect(screen.getAllByText(/политика/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/ФЗ-152/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders case-studies page", async () => {
    const Page = require("@/app/case-studies/page").default;
    render(<Page />);
    // "кейсы" встречается в заголовке, тегах и кнопке
    expect(screen.getAllByText(/кейсы/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders services page", async () => {
    const Page = require("@/app/services/page").default;
    render(<Page />);
    expect(screen.getByText(/услуги/i)).toBeInTheDocument();
    // "SEO" встречается в заголовке и в фичах
    expect(screen.getAllByText(/SEO/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders about page with stats", async () => {
    const Page = require("@/app/about/page").default;
    render(<Page />);
    expect(screen.getByText(/команда/i)).toBeInTheDocument();
    expect(screen.getByText("50+")).toBeInTheDocument();
  });

  it("renders blog placeholder page", async () => {
    const Page = require("@/app/blog/page").default;
    render(<Page />);
    expect(screen.getByText(/скоро/i)).toBeInTheDocument();
  });

  it("renders contact page", async () => {
    const Page = require("@/app/contact/page").default;
    render(<Page />);
    // "консультацию" встречается и в заголовке, и в кнопке
    expect(screen.getAllByText(/консультацию/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders 404 page", async () => {
    const Page = require("@/app/not-found").default;
    render(<Page />);
    expect(screen.getByText(/404/i)).toBeInTheDocument();
  });

  it("renders error page with reset button", async () => {
    const Page = require("@/app/error").default;
    render(<Page error={new Error("test")} reset={jest.fn()} />);
    expect(screen.getByText(/ошиб/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /попробовать/i })).toBeInTheDocument();
  });
});
