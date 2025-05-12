import frappeUIPreset from "frappe-ui/src/tailwind/preset"

export default {
  presets: [frappeUIPreset],
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
    "../node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
  ],
  variants: {
    extend: {
      display: ["group-hover"],
    },
  },
  theme: {
    fontFamily: {
      "fd-sans": ["InterVar", "sans-serif"],
      "fd-serif": ["Lora", "serif"],
      "fd-mono": ["Geist Mono", "serif"],
      "fd-round": ["Nunito", "serif"],
    },
    extend: {
      typography: (theme) => ({
        DEFAULT: {
          css: {
            "--tw-prose-body": theme("colors.gray.800"),
            blockquote: {
              fontStyle: "normal",
            },
          },
        },
        quoteless: {
          css: {
            "blockquote p:first-of-type::before": { content: "none" },
            "blockquote p:first-of-type::after": { content: "none" },
          },
        },
        sm: {
          css: {
            fontSize: "1em",
            fontWeight: 400,
            lineHeight: 1.5,
            letterSpacing: "0.02em",
            h1: {
              fontSize: "1.8em",
              fontWeight: 600,
            },
            "h1 > strong": {
              fontWeight: 800,
            },
            h2: {
              fontWeight: 600,
            },
            "h2 > strong": {
              fontWeight: 800,
            },
            h3: {
              fontWeight: 600,
            },
            "h3 > strong": {
              fontWeight: 800,
            },
            h4: {
              fontWeight: 600,
            },
            "h4 > strong": {
              fontWeight: 800,
            },
            h5: {
              fontSize: "0.9rem",
              fontWeight: 400,
            },
            "h5 > strong": {
              fontWeight: 600,
            },
            p: {
              marginTop: "1.4rem",
              marginBottom: "1.4rem",
            },
            "> ul > li p": {
              marginTop: "0.5rem",
              marginBottom: "0.5rem",
            },
            "> ul > li > *:first-child": {
              marginTop: "0.5rem",
            },
            "> ul > li > *:last-child": {
              marginBottom: "0.5rem",
            },
            "> ol > li p": {
              marginTop: "0.5rem",
              marginBottom: "0.5rem",
            },
            "> ol > li > *:first-child": {
              marginTop: "0.5rem",
            },
            "> ol > li > *:last-child": {
              marginBottom: "0.5rem",
            },
          },
        },
      }),
    },
  },
  plugins: [],
}
