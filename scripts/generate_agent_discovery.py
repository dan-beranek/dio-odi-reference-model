#!/usr/bin/env python3
"""Generate and validate the DIO/ODI domain-level agent discovery manifests.

A single reviewed source catalog is projected into two independent formats:
ARD v0.91 and Common AI Catalog v0.9. The upstream Server Card is validated
against a pinned snapshot of the experimental MCP Server Card schema.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "discovery/catalog-source.json"
ARD_SCHEMA = ROOT / "discovery/schemas/ard-entry.schema.json"
CARD_SCHEMA = ROOT / "discovery/schemas/server-card.schema.json"
CARD_FIXTURE = ROOT / "discovery/examples/mcp-server-card.json"
ARD_OUTPUT = ROOT / ".well-known/ard.json"
AI_CATALOG_OUTPUT = ROOT / ".well-known/ai-catalog.json"

ARD_CONTEXT = "https://agenticresourcediscovery.org/context/v1"
AI_CATALOG_SPEC_VERSION = "0.9"
AI_CATALOG_ENTRY_FIELDS = (
    "identifier", "displayName", "type", "url", "data",
    "description", "version", "tags", "publisher", "trustManifests",
    "extensions",
)
MEDIA_TYPE = re.compile(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path.relative_to(ROOT)}: {exc}") from exc


def dump_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def require_https(value: str, label: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{label} must be an absolute HTTPS URL: {value!r}")


def validate_source(source: dict) -> None:
    if not isinstance(source, dict):
        raise ValueError("Discovery catalog source must be a JSON object.")
    if source.get("source_version") != "0.1.0":
        raise ValueError("Unexpected discovery source_version; review and update the generator deliberately.")
    publisher = source.get("publisher")
    if not isinstance(publisher, dict) or not publisher.get("displayName"):
        raise ValueError("The canonical publisher requires a displayName.")
    if not publisher.get("identifier"):
        raise ValueError("The canonical publisher requires an identifier.")
    require_https(publisher.get("documentationUrl", ""), "publisher.documentationUrl")

    entries = source.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("The canonical source must contain at least one entry.")

    identifiers: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"entries[{index}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{label} must be an object.")
        for field in ("identifier", "displayName", "type", "description", "tags", "representativeQueries"):
            if field not in entry:
                raise ValueError(f"{label} is missing {field}.")
        identifier = entry["identifier"]
        if identifier in identifiers:
            raise ValueError(f"Duplicate discovery identifier: {identifier}")
        identifiers.add(identifier)
        if not identifier.startswith("urn:air:danielberanek.cz:"):
            raise ValueError(f"{label}.identifier must use the publisher's domain-anchored urn:air namespace.")
        if not MEDIA_TYPE.match(entry["type"]):
            raise ValueError(f"{label}.type must be a media type.")
        if ("url" in entry) == ("data" in entry):
            raise ValueError(f"{label} must contain exactly one of url or data.")
        if "url" in entry:
            require_https(entry["url"], f"{label}.url")
        queries = entry["representativeQueries"]
        if not isinstance(queries, list) or not 2 <= len(queries) <= 5:
            raise ValueError(f"{label}.representativeQueries must contain 2–5 natural-language examples.")
        if any(not isinstance(query, str) or not query.strip() for query in queries):
            raise ValueError(f"{label}.representativeQueries contains an empty or non-string value.")
        if not isinstance(entry["tags"], list) or any(not isinstance(tag, str) or not tag.strip() for tag in entry["tags"]):
            raise ValueError(f"{label}.tags must be an array of non-empty strings.")


def project_ard(source: dict) -> dict:
    entries = []
    for entry in source["entries"]:
        projected = {
            "@context": ARD_CONTEXT,
            "identifier": entry["identifier"],
            "displayName": entry["displayName"],
            "type": entry["type"],
        }
        if "url" in entry:
            projected["url"] = entry["url"]
        else:
            projected["data"] = entry["data"]
        projected["description"] = entry["description"]
        if entry.get("version"):
            projected["version"] = entry["version"]
        projected["tags"] = entry["tags"]
        if entry.get("capabilities"):
            projected["capabilities"] = entry["capabilities"]
        projected["representativeQueries"] = entry["representativeQueries"]
        entries.append(projected)
    return {"entries": entries}


def project_ai_catalog(source: dict) -> dict:
    entries = []
    for entry in source["entries"]:
        projected = {
            key: entry[key]
            for key in AI_CATALOG_ENTRY_FIELDS
            if key in entry
        }
        entries.append(projected)
    return {
        "specVersion": AI_CATALOG_SPEC_VERSION,
        "host": source["publisher"],
        "entries": entries,
    }


def validate_ard(manifest: dict) -> None:
    schema = read_json(ARD_SCHEMA)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
    if errors:
        summary = "; ".join(
            f"{'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ValueError(f"ARD v0.91 schema validation failed: {summary}")
    for index, entry in enumerate(manifest["entries"]):
        query_count = len(entry.get("representativeQueries", []))
        if not 2 <= query_count <= 5:
            raise ValueError(f"ARD entry {index} must include 2–5 representativeQueries.")


def validate_ai_catalog(catalog: dict) -> None:
    """Validate the published v0.9 RC contract; no official JSON Schema is published."""
    if not isinstance(catalog, dict):
        raise ValueError("AI Catalog must be an object.")
    if catalog.get("specVersion") != AI_CATALOG_SPEC_VERSION:
        raise ValueError("AI Catalog v0.9 RC must set specVersion to '0.9'.")
    if not isinstance(catalog.get("entries"), list):
        raise ValueError("AI Catalog must include an entries array.")
    host = catalog.get("host")
    if not isinstance(host, dict) or not isinstance(host.get("displayName"), str) or not host["displayName"].strip():
        raise ValueError("Discoverable AI Catalog requires host.displayName.")
    for index, entry in enumerate(catalog["entries"]):
        label = f"AI Catalog entries[{index}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{label} must be an object.")
        for field in ("identifier", "type"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f"{label} requires a non-empty {field}.")
        if ("url" in entry) == ("data" in entry):
            raise ValueError(f"{label} must contain exactly one of url or data.")
        if "url" in entry:
            require_https(entry["url"], f"{label}.url")
        if not MEDIA_TYPE.match(entry["type"]):
            raise ValueError(f"{label}.type must be a media type.")
        if "displayName" in entry and (not isinstance(entry["displayName"], str) or not entry["displayName"].strip()):
            raise ValueError(f"{label}.displayName must be a non-empty string when present.")


def validate_server_card(source: dict) -> None:
    card = read_json(CARD_FIXTURE)
    schema_source = read_json(CARD_SCHEMA)
    schema = {
        "$schema": schema_source["$schema"],
        "$ref": "#/$defs/ServerCard",
        "$defs": schema_source["$defs"],
    }
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(card)

    mcp_entry = next(
        (entry for entry in source["entries"] if entry["identifier"] == "urn:air:danielberanek.cz:mcp:dio-odi-reference"),
        None,
    )
    if mcp_entry is None:
        raise ValueError("The canonical source is missing the DIO/ODI MCP entry.")
    if card.get("version") != mcp_entry.get("version"):
        raise ValueError("Server Card version and canonical discovery entry version do not match.")
    remote = card.get("remotes", [{}])[0]
    if remote.get("url") != "https://mcp.danielberanek.cz/mcp":
        raise ValueError("Server Card remote URL does not match the deployed MCP endpoint.")
    if mcp_entry.get("url") != "https://mcp.danielberanek.cz/mcp/server-card":
        raise ValueError("ARD/AI Catalog MCP entry does not point to the deployed Server Card endpoint.")


def expected_outputs() -> dict[Path, str]:
    source = read_json(SOURCE)
    validate_source(source)
    validate_server_card(source)
    ard = project_ard(source)
    ai_catalog = project_ai_catalog(source)
    validate_ard(ard)
    validate_ai_catalog(ai_catalog)
    return {
        ARD_OUTPUT: dump_json(ard),
        AI_CATALOG_OUTPUT: dump_json(ai_catalog),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the generated public manifests")
    mode.add_argument("--check", action="store_true", help="verify committed manifests are reproducible")
    args = parser.parse_args()

    try:
        outputs = expected_outputs()
        if args.write:
            for path, content in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
                print(f"WROTE {path.relative_to(ROOT)}")
        else:
            stale = []
            for path, content in outputs.items():
                if not path.is_file() or path.read_text(encoding="utf-8") != content:
                    stale.append(str(path.relative_to(ROOT)))
            if stale:
                raise ValueError("Generated discovery manifests are stale or missing: " + ", ".join(stale))
            print("ARD and AI Catalog manifests are reproducible and valid.")
    except Exception as exc:
        print(f"Agent discovery generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
