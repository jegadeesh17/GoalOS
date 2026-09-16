import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: null,
      // FastAPI serves the SPA at /app and hashed bundles at /assets, so the worker
      // must live at root scope to control both.
      filename: 'sw.js',
      scope: '/',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'GoalOS — Executive Life Operating System',
        short_name: 'GoalOS',
        description:
          'Privacy-first, local-first executive OS for coaching, horizon alignment, and cognitive memory retrieval.',
        theme_color: '#065f46',
        background_color: '#f8faf8',
        display: 'standalone',
        start_url: '/app',
        scope: '/',
        icons: [
          { src: '/favicon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,woff,woff2}'],
        // Must name a URL that is actually in the precache manifest; the built
        // shell is precached as /index.html, which the API also serves at root.
        navigateFallback: '/index.html',
        // API traffic is never precached; only explicit runtime rules below apply.
        navigateFallbackDenylist: [/^\/api\//, /^\/docs/, /^\/openapi\.json/],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.(googleapis|gstatic)\.com\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts',
              expiration: { maxEntries: 20, maxAgeSeconds: 60 * 60 * 24 * 365 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Read-only journal/calendar GETs stay readable offline; writes always hit the network.
            urlPattern: ({ url, request }) =>
              request.method === 'GET' && /^\/api\/(journal|calendar|goals|settings)/.test(url.pathname),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'goalos-api-reads',
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 60, maxAgeSeconds: 60 * 60 * 24 },
              cacheableResponse: { statuses: [200] },
            },
          },
        ],
      },
      devOptions: { enabled: false },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
