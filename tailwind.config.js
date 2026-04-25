/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
    "./node_modules/flowbite/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#ffffff",
          100: "#f4f4f4",
          200: "#e3e3e3",
          300: "#cfcfcf",
          400: "#a3a3a3",
          500: "#7a7a7a",
          600: "#5c5c5c",
          700: "#404040",
          800: "#262626",
          900: "#111111",
          950: "#000000"
        },
        ink: {
          950: "#000000"
        }
      },
      boxShadow: {
        glow: "0 0 0 rgba(0, 0, 0, 0)"
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("flowbite/plugin")
  ]
};
