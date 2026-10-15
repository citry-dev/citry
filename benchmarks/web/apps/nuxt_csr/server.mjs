const port = Number(process.argv[2]);
if (!Number.isInteger(port) || port < 1024) throw new Error("A benchmark port is required");
process.env.NITRO_PORT = String(port);
process.env.PORT = String(port);
process.env.NITRO_HOST = "127.0.0.1";
process.env.HOST = "127.0.0.1";
await import("./.output/server/index.mjs");
