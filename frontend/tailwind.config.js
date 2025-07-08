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
      sans: ["InterVar", "sans-serif"],
      serif: ["Lora", "serif"],
      mono: ["Geist Mono", "serif"],
      round: ["Nunito", "serif"],
      // Only accessible in the editor
      inter: ["var(--font-inter)"],
      lora: ["var(--font-lora)"],
      roboto: ["var(--font-roboto)"],
      merriweather: ["var(--font-merriweather)"],
      geist: ["var(--font-geist)"],
      "ibm-plex": ["var(--font-ibm-plex)"],
      "eb-garamond": ["var(--font-eb-garamond)"],
      jetbrains: ["var(--font-jetbrains)"],
      comfortaa: ["var(--font-comfortaa)"],
      caveat: ["var(--font-caveat)"],
      "comic-sans": ["var(--font-comic-sans)"],
      nunito: ["var(--font-nunito)"],
    },
  },
  plugins: [],
}
