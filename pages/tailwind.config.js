/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: "hsl(var(--card))",
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        destructive: "hsl(var(--destructive))",
        'yr-accent': "hsl(var(--yr-accent))",
        'yr-accent-soft': "hsl(var(--yr-accent-soft))",
        'yr-sidebar': "hsl(var(--yr-sidebar))",
        'yr-surface': "hsl(var(--yr-surface))",
        'yr-hover': "hsl(var(--yr-hover))",
        'yr-composer': "hsl(var(--yr-composer))",
        'yr-text-subtle': "hsl(var(--yr-text-subtle))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      }
    },
  },
  plugins: [],
}
