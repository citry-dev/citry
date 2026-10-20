// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt({
  // The page's component has a one-word name (Card), which most Nuxt
  // projects allow; the default rule would flag the clean app.
  rules: { 'vue/multi-word-component-names': 'off' },
})
