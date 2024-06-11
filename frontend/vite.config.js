import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"
import { webserver_port } from "../../../sites/common_site_config.json"

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 8080,
    proxy: {
      "^/(app|login|api|assets|files)": {
        // Localhost resolution changes in Node 17
        target: `http://127.0.0.1:${webserver_port}`,
        ws: true,
        router: function (req) {
          const site_name = req.headers.host.split(":")[0]
          return `http://${site_name}:${webserver_port}`
        },
      },
    },
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
