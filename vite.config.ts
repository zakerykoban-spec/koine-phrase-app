import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/koine-phrase-app/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: [
        'apple-touch-icon.png',
        'apple-touch-icon-precomposed.png',
        'koine-icon-192-v2.png',
        'koine-icon-512-v2.png',
        'koine-icon-maskable-512-v2.png',
      ],
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
            src: 'koine-icon-192-v2.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'koine-icon-512-v2.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: 'koine-icon-maskable-512-v2.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true,
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
        globPatterns: ['**/*.{js,css,html,svg,png,webmanifest}'],
      },
    }),
  ],
})
