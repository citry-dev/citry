export default defineEventHandler(event => {
  setHeader(event, "cache-control", "no-store");
  setHeader(event, "content-type", "text/plain");
  return process.env.CITRY_BENCH_SERVER_NONCE || "ok";
});
