/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f5f3ff",
          100: "#ede9fe",
          200: "#ddd6fe",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
        },
        accent: {
          50: "#f0fdf4",
          100: "#dcfce7",
          400: "#5cd65c",
          500: "#4caf50",
          600: "#43a047",
          700: "#2e7d32",
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(124, 58, 237, 0.15)",
      },
    },
  },
  plugins: [],
};
