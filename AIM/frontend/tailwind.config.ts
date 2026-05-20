import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#010102",
        accent: "#5e6ad2",
        "accent-hover": "#828fff",
        "surface-1": "#0f1011",
        "surface-2": "#141516",
        "surface-3": "#18191a",
        "surface-4": "#191a1b",
        "border-hairline": "#23252a",
        "border-strong": "#34343a",
        ink: "#f7f8f8",
        "text-muted": "#d0d6e0",
        "text-subtle": "#8a8f98",
        "text-tertiary": "#62666d",
        "semantic-success": "#10b981",
        "semantic-error": "#ef4444",
        "semantic-warning": "#f59e0b",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xs: "4px",
        sm: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
        xxl: "24px",
        pill: "9999px",
      },
      letterSpacing: {
        "display-tight": "-0.03em",
        "display-medium": "-0.02em",
        heading: "-0.01em",
      },
    },
  },
  plugins: [],
};

export default config;
