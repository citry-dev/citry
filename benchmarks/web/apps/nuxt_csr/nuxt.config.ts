export default defineNuxtConfig({
  ssr: false,
  devtools: {enabled: false},
  telemetry: false,
  experimental: {payloadExtraction: false},
  app: {head: {link: [{rel: "stylesheet", href: "/assets/board.css"}]}},
});
