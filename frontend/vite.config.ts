import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:9000',
      '/sse': 'http://localhost:9000',
      '/messages': 'http://localhost:9000',
    },
  },
})
