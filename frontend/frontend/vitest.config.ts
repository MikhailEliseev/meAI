import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    css: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
      '@/components': path.resolve(__dirname, './components'),
      '@/lib': path.resolve(__dirname, './lib'),
      '@/hooks': path.resolve(__dirname, './hooks'),
      '@/app': path.resolve(__dirname, './app'),
      'lucide-react': path.resolve(__dirname, './tests/mocks/lucide-react.ts'),
      'cmdk': path.resolve(__dirname, './tests/mocks/cmdk.tsx'),
    },
  },
  define: {
    'global.ResizeObserver': class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  },
})
