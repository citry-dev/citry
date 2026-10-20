// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    // Private keys are only available on the server.
    secretToken: 's3cr3t',
    // Keys within public are also exposed to the browser.
    public: {
      apiBase: '/api',
    },
  },

  modules: ['@nuxt/eslint'],
})