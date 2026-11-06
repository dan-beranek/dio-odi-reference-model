import { createServer as createHttpServer } from 'node:http';
import { createMcpHandler } from '@modelcontextprotocol/server';
import { toNodeHandler } from '@modelcontextprotocol/node';
import { createDioOdiServer } from './server.js';
import { DEFAULT_EXPECTED_VERSION, DEFAULT_SOURCE_REF } from './data.js';

const port = Number(process.env.PORT ?? 3000);
if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error('PORT must be an integer between 1 and 65535.');
}

const allowedHosts = new Set(
  (process.env.MCP_ALLOWED_HOSTS ?? 'localhost:' + port + ',127.0.0.1:' + port)
    .split(',').map((value) => value.trim().toLowerCase()).filter(Boolean)
);
const allowedOrigins = new Set(
  (process.env.MCP_ALLOWED_ORIGINS ?? '').split(',').map((value) => value.trim()).filter(Boolean)
);

const sourceOptions = {
  sourceRef: process.env.DIO_ODI_SOURCE_REF ?? DEFAULT_SOURCE_REF,
  expectedVersion: process.env.DIO_ODI_EXPECTED_VERSION ?? DEFAULT_EXPECTED_VERSION
};
const handler = createMcpHandler(() => createDioOdiServer(sourceOptions));
const mcpHandler = toNodeHandler(handler);

const httpServer = createHttpServer((request, response) => {
  const host = request.headers.host?.toLowerCase();
  if (!host || !allowedHosts.has(host)) {
    response.writeHead(421, { 'content-type': 'application/json; charset=utf-8' });
    response.end(JSON.stringify({ error: 'Unrecognized Host header.' }));
    return;
  }

  const origin = request.headers.origin;
  if (origin && !allowedOrigins.has(origin)) {
    response.writeHead(403, { 'content-type': 'application/json; charset=utf-8' });
    response.end(JSON.stringify({ error: 'Origin is not in MCP_ALLOWED_ORIGINS.' }));
    return;
  }

  const url = new URL(request.url ?? '/', 'http://' + host);
  if (url.pathname === '/health' && request.method === 'GET') {
    response.writeHead(200, {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store'
    });
    response.end(JSON.stringify({ status: 'ok', server: 'dio-odi-reference-model', version: '0.1.0', read_only: true }));
    return;
  }
  if (url.pathname !== '/mcp') {
    response.writeHead(404, { 'content-type': 'application/json; charset=utf-8' });
    response.end(JSON.stringify({ error: 'Not found. MCP endpoint: /mcp' }));
    return;
  }

  if (origin) {
    response.setHeader('Access-Control-Allow-Origin', origin);
    response.setHeader('Access-Control-Expose-Headers', 'MCP-Protocol-Version, MCP-Session-Id');
    response.setHeader('Vary', 'Origin');
  }
  if (request.method === 'OPTIONS' && origin) {
    response.writeHead(204, {
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, MCP-Protocol-Version, MCP-Session-Id, Last-Event-Id',
      'Access-Control-Max-Age': '600'
    });
    response.end();
    return;
  }

  const normalizedRequest = Object.assign(request, { method: request.method ?? 'GET' });
  mcpHandler(normalizedRequest, response);
});

httpServer.listen(port, '127.0.0.1', () => {
  console.error('DIO/ODI MCP HTTP server listening on http://127.0.0.1:' + port + '/mcp (read-only).');
});

for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.once(signal, () => httpServer.close(() => process.exit(0)));
}
