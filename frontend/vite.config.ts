import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { visualizer } from 'rollup-plugin-visualizer';
import type { Manifest } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Bundle analyzer plugin
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/pages': path.resolve(__dirname, './src/pages'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/stores': path.resolve(__dirname, './src/stores'),
      '@/lib': path.resolve(__dirname, './src/lib'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/app': path.resolve(__dirname, './src/app'),
      '@/entities': path.resolve(__dirname, './src/entities'),
      '@/features': path.resolve(__dirname, './src/features'),
      '@/widgets': path.resolve(__dirname, './src/widgets'),
      '@/shared': path.resolve(__dirname, './src/shared'),
      '@/processes': path.resolve(__dirname, './src/processes'),
    },
  },
  server: {
    port: 3000,
    open: true,
    host: true,
    hmr: {
      overlay: true,
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV === 'development',
    target: 'es2020',
    minify: 'terser',
    cssMinify: true,
    reportCompressedSize: true,
    chunkSizeWarningLimit: 1000,
    assetsInlineLimit: 4096, // Inline assets smaller than 4kb
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching and loading
        manualChunks: {
          // React ecosystem
          react: ['react', 'react-dom', 'react-router-dom'],
          // Query library
          query: ['@tanstack/react-query'],
          // UI components
          ui: [
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-select',
            '@radix-ui/react-tabs',
            '@radix-ui/react-toast',
            '@radix-ui/react-tooltip',
            '@radix-ui/react-switch',
            '@radix-ui/react-progress',
            '@radix-ui/react-checkbox',
          ],
          // Monaco Editor (heavy)
          monaco: ['@monaco-editor/react'],
          // Charts
          charts: ['recharts'],
          // Forms
          forms: ['react-hook-form', '@hookform/resolvers', 'zod'],
          // State management
          state: ['zustand'],
          // Date utilities
          date: ['date-fns'],
          // Icons
          icons: ['@heroicons/react', 'lucide-react'],
        },
        // Optimized chunk naming for better caching
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
            ? chunkInfo.facadeModuleId.split('/').pop()?.replace(/\.[jt]sx?$/, '') || 'chunk'
            : 'chunk';
          return `js/[name]-[hash].js`;
        },
        // Asset naming
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name!.split('.');
          const ext = info[info.length - 1];
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name!)) {
            return `images/[name]-[hash].${ext}`;
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name!)) {
            return `fonts/[name]-[hash].${ext}`;
          }
          return `assets/[name]-[hash].${ext}`;
        },
      },
      // External dependencies that should not be bundled
      external: (id) => {
        // Keep all node_modules external in development for faster builds
        return id.startsWith('.') || id.startsWith('/');
      },
    },
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: process.env.NODE_ENV === 'production',
        pure_funcs: process.env.NODE_ENV === 'production' ? ['console.log', 'console.info'] : [],
        passes: 2,
      },
      mangle: {
        safari10: true,
      },
      format: {
        safari10: true,
        comments: false,
      },
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'zustand',
      '@heroicons/react/24/outline',
      'lucide-react',
    ],
    // Pre-bundle dependencies for faster dev server startup
    esbuildOptions: {
      target: 'es2020',
    },
  },
  // Performance hints
  define: {
    // Enable development mode optimizations
    __DEV__: process.env.NODE_ENV === 'development',
    // Enable performance monitoring in development
    __PERF__: process.env.NODE_ENV === 'development',
  },
  // CSS optimization
  css: {
    devSourcemap: process.env.NODE_ENV === 'development',
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
      },
    },
  },
  // Experimental features for better performance
  experimentalFeatures: {
    // Enable persistent cache for faster builds
    persistentCache: true,
  },
});
