export default defineNuxtConfig({
  ssr: true,
  devtools: {enabled: false},
  telemetry: false,
  experimental: {payloadExtraction: false},
  app: {head: {link: [{rel: "stylesheet", href: "/assets/board.css"}]}},
});
