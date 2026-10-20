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

  // Off by default. The benchmark turns them on because other frameworks
  // here run the same kind of check: unknown components, attributes,
  // directives and events in templates, and typed links.
  typescript: {
    tsConfig: {
      vueCompilerOptions: { strictTemplates: true },
    },
  },
  experimental: { typedPages: true },
})