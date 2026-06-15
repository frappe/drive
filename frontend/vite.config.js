import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { getLocalFrappeUIDevConfig, importFrappeUIPlugin } from './vite-helpers'

export default defineConfig(async ({ mode }) => {
  console.log(mode)
  const { useLocalFrappeUI, localFrappeUIAliases } = getLocalFrappeUIDevConfig({
    mode,
    rootDir: __dirname,
  })
  
  const frappeui = await importFrappeUIPlugin({ useLocalFrappeUI })

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
        '@icons': path.resolve(__dirname, '../drive/public/images/icons'),
        'tailwind.config.js': path.resolve(__dirname, 'tailwind.config.js'),
        ...localFrappeUIAliases,
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
        allow: ['..', 'node_modules', '../frappe-ui'],
      },
    },
    ssr: {
      external: ['html2canvas', 'dompurify'],
    },
    optimizeDeps: {
      include: ['frappe-ui > feather-icons', 'frappe-ui > lowlight', 'yjs', 'tailwind.config.js'],
    },
  }
  return config
})
