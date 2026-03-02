import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import frappeui from 'frappe-ui/vite'

export default defineConfig(async () => {
  const config = {
    define: {
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
    },
    plugins: [
      frappeui({
        frappeProxy: true,
        lucideIcons: true,
        jinjaBootData: true,
        buildConfig: {
          indexHtmlPath: '../drive/www/drive.html',
        },
      }),
      vue(),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        'tailwind.config.js': path.resolve(__dirname, 'tailwind.config.js'),
      },
      dedupe: ['yjs'],
    },
    build: {
      sourcemap: true,
      outDir: `../${path.basename(path.resolve('..'))}/public/frontend`,
      emptyOutDir: true,
      target: 'esnext',
      commonjsOptions: {
        include: [/tailwind.config.js/, /node_modules/],
      },
    },
    server: {
      allowedHosts: ['drive.localhost'],
      fs: {
        allow: ['..'],
      },
    },
    ssr: {
      external: { html2canvas: 'html2canvas', dompurify: 'dompurify' },
    },
    optimizeDeps: {
      esbuildOptions: { target: 'esnext' },
      include: ['frappe-ui > feather-icons', 'frappe-ui > lowlight', 'yjs'],
    },
  }
  return config
})
