import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  root: fileURLToPath(new URL('.', import.meta.url)),
  plugins: [vue()],
  resolve: { alias: [
    { find: '@/lib/supabase', replacement: fileURLToPath(new URL('./mocks.ts', import.meta.url)) },
    { find: '@/lib/services', replacement: fileURLToPath(new URL('./mocks.ts', import.meta.url)) },
    { find: '@', replacement: fileURLToPath(new URL('../../src', import.meta.url)) },
  ] },
  server: { host: '127.0.0.1', port: 5179, strictPort: true },
})
