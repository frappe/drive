import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"
import frappeui from "frappe-ui/vite"

export default defineConfig({
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
    target: "es2015",
    minify: 'esbuild',
    chunkSizeWarningLimit: 1500,
    commonjsOptions: {
      include: [/tailwind.config.js/, /node_modules/],
    },
    rollupOptions: {
      maxParallelFileOps: 1,
      maxParallelFileReads: 1,
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            if (id.includes('@tiptap')) return 'editor';
            if (id.includes('mammoth')) return 'office-mammoth';
            if (id.includes('xlsx')) return 'office-xlsx';
            if (id.includes('docx-preview')) return 'office-docx';
            if (id.includes('x-data-spreadsheet')) return 'spreadsheet';
            if (id.includes('frappe-ui')) return 'frappe-ui';
            if (id.includes('vue') || id.includes('@vue')) return 'vue-vendor';
            if (id.includes('yjs') || id.includes('y-')) return 'collaboration';
            
            return 'vendor';
          }
        }
      }
    },
  },
  server: {
    allowedHosts: ["drive.localhost"],
  },
  ssr: {
    external: { html2canvas: "html2canvas", dompurify: "dompurify" },
  },
  optimizeDeps: {
    esbuildOptions: { 
      target: "es2015",
      keepNames: false,
      treeShaking: true,
    },
    include: ["feather-icons", "showdown", "tailwind.config.js", "lowlight"],
    exclude: ['mammoth', 'xlsx', 'docx-preview', 'x-data-spreadsheet']
  },
})
