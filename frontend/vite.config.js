import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"
import fs from "fs"

function getCommonSiteConfig() {
  let currentDir = path.resolve('.')
  // traverse up till we find frappe-bench with sites directory
  while (currentDir !== '/') {
    if (
      fs.existsSync(path.join(currentDir, 'sites')) &&
      fs.existsSync(path.join(currentDir, 'apps'))
    ) {
      let configPath = path.join(currentDir, 'sites', 'common_site_config.json')
      if (fs.existsSync(configPath)) {
        return JSON.parse(fs.readFileSync(configPath))
      }
      return null
    }
    currentDir = path.resolve(currentDir, '..')
  }
  return null
}

const config = getCommonSiteConfig()
const webserver_port = config ? config.webserver_port : 8000
if (!config) {
  console.log('No common_site_config.json found, using default port 8000')
}

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
