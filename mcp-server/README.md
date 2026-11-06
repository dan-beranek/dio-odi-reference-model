# DIO/ODI Reference Model — MCP server

Read-only Model Context Protocol server for the archived **DIO/ODI Reference Model v0.7.0**.

- Release DOI: https://doi.org/10.5281/zenodo.24020300
- Canonical vocabulary namespace: https://vocab.danielberanek.cz/dio-odi/#
- Reference Model repository: https://github.com/dan-beranek/dio-odi-reference-model
- Reference data licence: CC BY 4.0
- MCP implementation licence: MIT

## Authority and scope

This server is a retrieval interface, not a second vocabulary or an ontology-authoring layer. It reads the immutable post-archive metadata commit `264bb30b66be051998b4eb522ae1af8d376e15d7`. The GitHub tag `v0.7.0` predates Zenodo DOI synchronization; the pinned follow-up commit contains the finalized DOI metadata while preserving the released vocabulary and mapping content.

The loader checks the model version, archived DOI, JSON-LD vocabulary version, and operational works registry before returning data. It reads only an explicit allow-list of source paths, bounds response size and fetch time, and caches the snapshot for the process lifetime.

The initial implementation is deliberately read-only. It has no create, update, delete, publication, or repository-write tools. Derived application mappings remain separate from the canonical SKOS vocabulary. No new concepts or relations are inferred.

## Requirements and local setup

- Node.js 20.19 or newer
- npm
- Network access to raw.githubusercontent.com for the pinned public source files

The implementation uses the official TypeScript MCP SDK v2, Zod 4, and supports stdio and Streamable HTTP.

```bash
cd mcp-server
npm install
npm run typecheck
npm test
npm run build
```

## Local stdio

```bash
npm run dev
```

For a built process, configure an MCP host to launch `node` with the absolute path to `mcp-server/dist/stdio.js`. Example configuration:

```json
{
  "mcpServers": {
    "dio-odi-reference-model": {
      "command": "node",
      "args": ["/absolute/path/to/dio-odi-reference-model/mcp-server/dist/stdio.js"],
      "env": {
        "DIO_ODI_SOURCE_REF": "264bb30b66be051998b4eb522ae1af8d376e15d7",
        "DIO_ODI_EXPECTED_VERSION": "0.7.0"
      }
    }
  }
}
```

The stdio process writes protocol messages to stdout and diagnostics only to stderr.

## Local Streamable HTTP

```bash
npm run dev:http
```

The Node adapter binds to `127.0.0.1:3000` by default:

- MCP: `http://127.0.0.1:3000/mcp`
- Health: `http://127.0.0.1:3000/health`

For a non-local hostname, configure both allow-lists explicitly:

```bash
PORT=3000 \
MCP_ALLOWED_HOSTS=mcp.example.org:3000 \
MCP_ALLOWED_ORIGINS=https://allowed-client.example \
npm run dev:http
```

The adapter checks the Host header and rejects browser Origin values not listed in `MCP_ALLOWED_ORIGINS`. It binds to loopback by default. Do not expose it directly to the public internet without TLS, an explicit host/origin policy, suitable authentication, and rate limiting at the reverse proxy or hosting layer. A read-only public endpoint can still be abused for resource exhaustion.

## Cloudflare Workers (remote endpoint)

The Worker entry point is `src/worker.ts`; configuration is in `wrangler.jsonc`. It provides a stateless Streamable HTTP endpoint at `/mcp` and a health endpoint at `/health`.

Before deployment, set `MCP_ALLOWED_HOSTS` to the exact Worker hostname in `wrangler.jsonc`. Leave the placeholder unchanged until a hostname is assigned; the Worker will reject requests when no valid host is configured. Optionally set `MCP_ALLOWED_ORIGINS` to exact browser origins. Add an authentication or edge-access policy and rate limits before public exposure.

```bash
npm run dev:worker
npm run deploy:worker
```

Remote deployment is not part of the source-code build and has not been performed.

## MCP tools

| Tool | Purpose |
|---|---|
| `get_reference_model_info` | Current archived model version, DOI, vocabulary version, source ref and licence |
| `search_concepts` | Search concept IDs, labels, definitions and scope notes |
| `get_concept` | Exact retrieval by URI, compact ID, local ID, preferred or alternative label |
| `list_concepts` | Paginated listing in stable identifier order |
| `list_application_mappings` | List derived mappings separately from the canonical vocabulary |
| `get_application_mapping` | Retrieve the full Markdown source of one mapping |
| `search_corpus_works` | Search registered DIO/ODI publications and software records |
| `get_corpus_work` | Retrieve a work record by stable work ID |

Concept resolution is exact. Ambiguous labels are reported rather than guessed; substring search does not invent concepts or relations.

## MCP resources

- `dio-odi://reference-model/metadata`
- `dio-odi://vocabulary/jsonld`
- `dio-odi://vocabulary/turtle`
- `dio-odi://reference-model/terminology`
- `dio-odi://reference-model/source-map`
- `dio-odi://corpus/works`
- `dio-odi://corpus/relations`
- `dio-odi://corpus/references`
- `dio-odi://mappings/index`
- `dio-odi://concepts/{identifier}` (resource template)

## Source pinning

Default source ref: `264bb30b66be051998b4eb522ae1af8d376e15d7`; expected model version: `0.7.0`.

Keep the source ref and expected version pinned together for reproducible integrations. Do not point production clients at `main`. Pointing to the original `v0.7.0` tag will fail closed because it predates synchronization of the version-specific Zenodo DOI.

## Validation

GitHub Actions runs dependency installation, strict typecheck, unit tests, the protocol-level integration test using the official MCP client, Node build, and a Cloudflare Worker dry run. Use the official [MCP Inspector](https://github.com/modelcontextprotocol/inspector) for manual host-level checks after installing dependencies:

```bash
npx @modelcontextprotocol/inspector npm run dev
```

Do not consider the server production-ready until the real dependency install, typecheck, tests and Inspector connection succeed on the target Node runtime. Remote deployment requires a separate hostname and security configuration.
