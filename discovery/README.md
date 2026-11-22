# DIO/ODI Agent Discovery

This directory contains the versioned source for the domain-level agent discovery manifests published from the DIO/ODI Reference Model site.

## Source of truth

- `catalog-source.json` is the single reviewed source for publisher and artifact metadata.
- `scripts/generate_agent_discovery.py` projects that source into the two independent formats below.
- The generated public files are `.well-known/ard.json` and `.well-known/ai-catalog.json`.

Do not edit generated manifest files by hand. Update the canonical source and regenerate them instead.

## Published discovery documents

- ARD v0.91 Proposal: https://vocab.danielberanek.cz/.well-known/ard.json
- Common AI Catalog v0.9 Release Candidate: https://vocab.danielberanek.cz/.well-known/ai-catalog.json
- DIO/ODI MCP Server Card (experimental MCP extension): https://mcp.danielberanek.cz/mcp/server-card

ARD and Common AI Catalog are separate discovery representations. ARD v0.91 uses `representativeQueries` and the `rel="ard"` / `Agentmap:` discovery mechanisms. Common AI Catalog v0.9 uses `specVersion: "0.9"`, a `host` object, `rel="ai-catalog"`, and the `application/ai-catalog+json` media type. The two manifests are generated from common source metadata but are not copies or aliases.

The MCP Server Card is a protocol-specific connection description. Its upstream extension is explicitly experimental and is not an accepted or official MCP extension. The card is validated against a pinned upstream schema snapshot and tested remotely after Worker deployment.

## Validation and publishing

Run locally or in GitHub Actions:

```bash
python scripts/generate_agent_discovery.py --write
python scripts/generate_agent_discovery.py --check
```

The generator validates ARD entries against the pinned upstream ARD JSON Schema, applies explicit checks to the Common AI Catalog v0.9 Release Candidate contract (the specification repository does not currently publish an official JSON Schema), and validates the Server Card fixture against its pinned experimental upstream schema.

GitHub Pages uses `_config.yml` to explicitly include the hidden `.well-known` directory. The public endpoint validator checks both URLs and their media types after deployment.

## Pinned upstream schema snapshots

- ARD entry/manifest JSON Schema: https://github.com/ards-project/ard-spec/blob/main/spec/schemas/ard-entry.schema.json (upstream commit `f073b1ea9b01a5f068d0b0986426f2ea49fa30b2`; ARD v0.91 Proposal).
- MCP Server Card JSON Schema: https://github.com/modelcontextprotocol/ext-server-card/blob/main/schema.json (upstream commit `28db12c9b4a379489d46e49bf1bd4a991f05c9b7`; experimental extension).
- Common AI Catalog v0.9 specification: https://ai-catalog.io/spec/ (Release Candidate for v1.0; validated against its published structural requirements).

The pinned schemas are snapshots for reproducible validation. Updating them requires an explicit review of the upstream specification revision and the generated manifests.
