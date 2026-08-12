import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/koine-phrase-app/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg'],
      manifest: {
        name: 'Διάλογοι Ἑλληνιστί',
        short_name: 'Koine',
        description: 'A focused Koine Greek phrase and mastery study app.',
        theme_color: '#151714',
        background_color: '#151714',
        display: 'standalone',
        lang: 'grc',
        start_url: '/koine-phrase-app/',
        scope: '/koine-phrase-app/',
        icons: [
          {
            src: 'icon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true,
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
        globPatterns: ['**/*.{js,css,html,svg,webmanifest}'],
      },
    }),
  ],
})
