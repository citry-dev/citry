export function GET() {
  return new Response(process.env.CITRY_BENCH_SERVER_NONCE || "ok", {
    headers: {"cache-control": "no-store", "content-type": "text/plain"},
  });
}
