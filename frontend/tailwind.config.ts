import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./pages/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "#f5f5f5", // Soft light gray from design.md
        foreground: "#333333", // Dark gray for high readability
        primary: {
          DEFAULT: "#ff9966", // Muted orange from design.md
          foreground: "#ffffff",
          hover: "#e6855c",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "#e8e8e8",
          foreground: "#666666",
        },
        accent: {
          DEFAULT: "#cc9900", // Soft gold from design.md
          foreground: "#ffffff",
          light: "#ffe066",
        },
        success: {
          DEFAULT: "#22c55e",
          foreground: "#ffffff",
          light: "#86efac",
        },
        warning: {
          DEFAULT: "#f59e0b",
          foreground: "#ffffff",
          light: "#fcd34d",
        },
        popover: {
          DEFAULT: "#ffffff",
          foreground: "#333333",
        },
        card: {
          DEFAULT: "#ffffff",
          foreground: "#333333",
        },
        sidebar: {
          DEFAULT: "#ffffff",
          foreground: "#333333",
          primary: "#ff9966",
          "primary-foreground": "#ffffff",
          accent: "#cc9900",
          "accent-foreground": "#ffffff",
          border: "#e8e8e8",
          ring: "#ff9966",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: {
            height: "0",
          },
          to: {
            height: "var(--radix-accordion-content-height)",
          },
        },
        "accordion-up": {
          from: {
            height: "var(--radix-accordion-content-height)",
          },
          to: {
            height: "0",
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
