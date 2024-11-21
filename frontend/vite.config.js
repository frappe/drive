import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"
import frappeui from "frappe-ui/vite"

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), frappeui()],
  define: {
    "process.env.IS_PREACT": JSON.stringify("true"),
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "tailwind.config.js": path.resolve(__dirname, "tailwind.config.js"),
    },
  },
  build: {
    sourcemap: true,
    outDir: `../${path.basename(path.resolve(".."))}/public/frontend`,
    emptyOutDir: true,
    target: "esnext",
    commonjsOptions: {
      include: [/tailwind.config.js/, /node_modules/],
    },
  },
  optimizeDeps: {
    esbuildOptions: { target: "esnext" },
    include: [
      "frappe-ui",
      "feather-icons",
      "showdown",
      "prosemirror",
      "tiptap",
      "engine.io-client",
      "tailwind.config.js",
    ],
  },
})
