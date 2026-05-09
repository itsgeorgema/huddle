import cors from "@fastify/cors";
import Fastify, { type FastifyReply, type FastifyRequest } from "fastify";
import { loadConfig } from "./config.js";

const config = loadConfig();
const app = Fastify({ logger: true });

await app.register(cors, {
  origin: config.corsOrigins,
  credentials: true
});

app.get("/health", async () => ({
  status: "ok",
  service: "huddle-api-gateway",
  agentsUrl: config.agentsUrl
}));

app.all("/api/*", async (request: FastifyRequest, reply: FastifyReply) => {
  const upstreamUrl = `${config.agentsUrl}${request.url}`;
  const headers = new Headers();
  for (const [key, value] of Object.entries(request.headers)) {
    if (!value || ["host", "content-length", "connection"].includes(key.toLowerCase())) {
      continue;
    }
    headers.set(key, Array.isArray(value) ? value.join(",") : String(value));
  }

  const method = request.method.toUpperCase();
  const hasBody = !["GET", "HEAD"].includes(method);
  const body =
    hasBody && request.body !== undefined
      ? typeof request.body === "string"
        ? request.body
        : JSON.stringify(request.body)
      : undefined;

  const upstream = await fetch(upstreamUrl, { method, headers, body });
  const contentType = upstream.headers.get("content-type");
  if (contentType) {
    reply.header("content-type", contentType);
  }
  reply.status(upstream.status);
  return contentType?.includes("application/json") ? upstream.json() : upstream.text();
});

app.setErrorHandler((error, _request, reply) => {
  app.log.error(error);
  const message = error instanceof Error ? error.message : "Unknown upstream error";
  reply.status(502).send({
    error: "gateway_upstream_error",
    message
  });
});

await app.listen({ host: config.host, port: config.port });
