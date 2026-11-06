import { createMcpHandler } from '@modelcontextprotocol/server';
import { createDioOdiServer } from './server.js';
import { DEFAULT_EXPECTED_VERSION, DEFAULT_SOURCE_REF } from './data.js';

interface WorkerEnv {
  DIO_ODI_SOURCE_REF?: string;
  DIO_ODI_EXPECTED_VERSION?: string;
  MCP_ALLOWED_HOSTS?: string;
  MCP_ALLOWED_ORIGINS?: string;
}

function csvSet(value: string | undefined, lowercase = false): Set<string> {
  const items = (value ?? '').split(',').map((item) => item.trim()).filter(Boolean);
  return new Set(lowercase ? items.map((item) => item.toLowerCase()) : items);
}

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
  });
}

export default {
  async fetch(request: Request, env: WorkerEnv): Promise<Response> {
    const url = new URL(request.url);
    const allowedHosts = csvSet(env.MCP_ALLOWED_HOSTS, true);
    if (allowedHosts.size === 0 || !allowedHosts.has(url.host.toLowerCase())) {
      return jsonResponse({ error: 'Host is not configured in MCP_ALLOWED_HOSTS.' }, 421);
    }

    if (url.pathname === '/health' && request.method === 'GET') {
      return jsonResponse({
        status: 'ok',
        server: 'dio-odi-reference-model',
        version: '0.1.0',
        read_only: true
      }, 200);
    }
    if (url.pathname !== '/mcp') {
      return jsonResponse({ error: 'Not found. MCP endpoint: /mcp' }, 404);
    }

    const origin = request.headers.get('Origin');
    const allowedOrigins = csvSet(env.MCP_ALLOWED_ORIGINS);
    if (origin && (allowedOrigins.size === 0 || !allowedOrigins.has(origin))) {
      return jsonResponse({ error: 'Origin is not in MCP_ALLOWED_ORIGINS.' }, 403);
    }

    const corsHeaders = new Headers();
    if (origin) {
      corsHeaders.set('Access-Control-Allow-Origin', origin);
      corsHeaders.set('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
      corsHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, MCP-Protocol-Version, MCP-Session-Id, Last-Event-Id');
      corsHeaders.set('Access-Control-Expose-Headers', 'MCP-Protocol-Version, MCP-Session-Id');
      corsHeaders.set('Access-Control-Max-Age', '600');
      corsHeaders.set('Vary', 'Origin');
    }
    if (request.method === 'OPTIONS' && origin) return new Response(null, { status: 204, headers: corsHeaders });

    const sourceOptions = {
      sourceRef: env.DIO_ODI_SOURCE_REF ?? DEFAULT_SOURCE_REF,
      expectedVersion: env.DIO_ODI_EXPECTED_VERSION ?? DEFAULT_EXPECTED_VERSION
    };
    const handler = createMcpHandler(() => createDioOdiServer(sourceOptions));
    const response = await handler.fetch(request);
    if (!origin) return response;

    const headers = new Headers(response.headers);
    corsHeaders.forEach((value, key) => headers.set(key, value));
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers
    });
  }
};
