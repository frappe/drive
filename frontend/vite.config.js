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
    minify: false,
    
    commonjsOptions: {
      include: [/tailwind.config.js/, /node_modules/],
    },
    
    rollupOptions: {
      maxParallelFileOps: 1,
      
      output: {
        manualChunks: (id) => {
          if (id.includes('node_modules')) {
            if (id.includes('@tiptap/core')) return 'tiptap-core';
            if (id.includes('@tiptap/vue')) return 'tiptap-vue';
            if (id.includes('@tiptap/starter-kit')) return 'tiptap-starter';
            if (id.includes('@tiptap/extension')) return 'tiptap-ext';
            if (id.includes('mammoth')) return 'mammoth';
            if (id.includes('xlsx')) return 'xlsx';
            if (id.includes('docx-preview')) return 'docx';
            if (id.includes('x-data-spreadsheet')) return 'spreadsheet';
            if (id.includes('frappe-ui')) return 'frappe';
            if (id.includes('vue-router')) return 'vue-router';
            if (id.includes('vue')) return 'vue';
            if (id.includes('yjs')) return 'yjs';
            if (id.includes('y-')) return 'y-collab';
            if (id.includes('@headlessui')) return 'headless';
            if (id.includes('socket.io')) return 'socketio';
            
            const hash = id.split('node_modules/')[1].substring(0, 8);
            return `vendor-${hash}`;
          }
        },
        
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
      },
            treeshake: false,
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
    },
    include: ["feather-icons", "showdown", "tailwind.config.js", "lowlight"],
    exclude: ['@tiptap/*', 'mammoth', 'xlsx', 'docx-preview', 'x-data-spreadsheet', 'yjs', 'y-*']
  },
})
