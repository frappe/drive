import frappeUIPreset from "frappe-ui/tailwind"

export default {
  presets: [frappeUIPreset],
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
    "../node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
  ],
  safelist: [
    "text-[13px]",
    "text-[14px]",
    "text-[15px]",
    "text-[16px]",
    "text-[17px]",
    "text-[18px]",
    "text-[18px]",
    "text-[19px]",
    "leading-[1.2]",
    "leading-[1.4]",
    "leading-[1.5]",
    "leading-[1.6]",
    "leading-[1.8]",
    "leading-[2]",
    "leading-[2.2]",
    "leading-[2.5]",
    "leading-[3]",
  ],
  variants: {
    extend: {
      display: ["group-hover"],
    },
  },
}
