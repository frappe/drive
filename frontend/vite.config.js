import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"

// https://vitejs.dev/config/
export default defineConfig(async ({ mode }) => {
  const isDev = mode === "development"
  const frappeui = await importFrappeUIPlugin(isDev)

  const config = {
    define: {
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: "false",
    },
    plugins: [
      frappeui({
        frappeProxy: true,
        lucideIcons: true,
        jinjaBootData: true,
        buildConfig: {
          indexHtmlPath: "../drive/www/drive.html",
        },
      }),
      vue(),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
        "tailwind.config.js": path.resolve(__dirname, "tailwind.config.js"),
      },
      dedupe: ["yjs"],
    },
    build: {
      sourcemap: true,
      outDir: `../${path.basename(path.resolve(".."))}/public/frontend`,
      emptyOutDir: true,
      target: "esnext",
      commonjsOptions: {
        include: [/tailwind.config.js/, /node_modules/],
      },
      rollupOptions: {
        // Ignore Frappe bench-specific imports that don't exist in standalone builds
        external: [
          /common_site_config\.json/,
          /\.\.\/\.\.\/\.\.\/frappe\//,  // Frappe core dependencies
        ],
      },
    },
    server: {
      allowedHosts: ["drive.localhost"],
      fs: {
        allow: [".."],
      },
    },
    ssr: {
      external: { html2canvas: "html2canvas", dompurify: "dompurify" },
    },
    optimizeDeps: {
      esbuildOptions: { target: "esnext" },
      include: ["frappe-ui > feather-icons", "frappe-ui > lowlight", "yjs"],
    },
  }
  if (isDev) {
    try {
      // Check if the local frappe-ui directory exists
      const fs = await import("node:fs")
      const localFrappeUIPath = path.resolve(__dirname, "../frappe-ui")
      if (fs.existsSync(localFrappeUIPath)) {
        config.resolve.alias["frappe-ui"] = localFrappeUIPath
      } else {
        console.warn("Local frappe-ui directory not found, using npm package")
      }
    } catch (error) {
      console.warn(
        "Error checking for local frappe-ui, using npm package:",
        error.message
      )
    }
  }
  return config
})
async function importFrappeUIPlugin(isDev) {
  if (isDev) {
    try {
      const module = await import("../frappe-ui/vite")
      return module.default
    } catch (error) {
      console.warn(
        "Local frappe-ui not found, falling back to npm package:",
        error.message
      )
    }
  }
  // Fall back to npm package if local import fails
  const module = await import("frappe-ui/vite")
  return module.default
}
