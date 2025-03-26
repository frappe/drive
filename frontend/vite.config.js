import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"
import frappeui from "frappe-ui/vite"

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true, // Setup proxy to Frappe backend
      lucideIcons: true, // Configure Lucide icons
      jinjaBootData: true, // Inject server-side boot data
      // Production build config for asset paths and HTML output
      buildConfig: {
        indexHtmlPath: "../drive/www/drive.html",
      },
    }),
    vue(),
  ],
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
    sourcemap: false,
    outDir: `../${path.basename(path.resolve(".."))}/public/frontend`,
    emptyOutDir: true,
    target: "esnext",
    commonjsOptions: {
      include: [/tailwind.config.js/, /node_modules/],
    },
    rollupOptions: {
      maxParallelFileOps: 2,
    },
  },
  server: {
    allowedHosts: ["drive.localhost"],
  },

  optimizeDeps: {
    esbuildOptions: { target: "esnext" },
    include: ["feather-icons", "showdown", "tailwind.config.js"],
  },
})
