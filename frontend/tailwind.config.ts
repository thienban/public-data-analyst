import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          500: "#3b82f6",
          600: "#2563eb",
          900: "#1e3a8a",
        },
        danger: "#ef4444",
        warning: "#f59e0b",
        success: "#22c55e",
      },
    },
  },
  plugins: [],
};

export default config;
