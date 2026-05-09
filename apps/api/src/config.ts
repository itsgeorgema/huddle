export type GatewayConfig = {
  host: string;
  port: number;
  agentsUrl: string;
  corsOrigins: string[];
};

export function loadConfig(): GatewayConfig {
  return {
    host: process.env.HOST || "0.0.0.0",
    port: Number(process.env.PORT || 8000),
    agentsUrl: process.env.AGENTS_URL || "http://localhost:8001",
    corsOrigins: (process.env.CORS_ORIGINS || "http://localhost:3000,http://127.0.0.1:3000")
      .split(",")
      .map((origin) => origin.trim())
      .filter(Boolean)
  };
}
