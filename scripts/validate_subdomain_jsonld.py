#!/usr/bin/env python3
"""Validate Reference Model page graphs against the pinned shared identity registry."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "metadata/entity-registry.lock.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / LOCK["snapshot_path"]).read_text(encoding="utf-8"))
if REGISTRY.get("status") != "canonical-approved" or REGISTRY.get("registry_version") != LOCK.get("registry_version"):
    raise SystemExit("Entity Registry snapshot is not approved or does not match its lock.")


def entity(key: str) -> dict:
    matches = [
        item for item in REGISTRY.get("entities", [])
        if item.get("key") == key and item.get("status") == "active"
    ]
    if len(matches) != 1:
        raise SystemExit("Entity Registry must contain exactly one active " + key + " record.")
    return matches[0]


PERSON = entity("person-daniel-beranek")
MODEL = entity("project-dio-odi-reference-model")
VOCAB = entity("vocabulary-dio-odi-reference")
PERSON_ID = PERSON["@id"]
PROFILE_URL = PERSON["url"]
ROOT_URL = MODEL["url"]
ROOT_PAGE = ROOT_URL + "#webpage"
MODEL_ID = MODEL["@id"]
VOCAB_URL = VOCAB["url"]
VOCAB_PAGE = VOCAB_URL + "#webpage"
VOCAB_ID = VOCAB["@id"]

PERSON_SURFACES = (
    "index.html",
    "dio-odi/index.html",
    "mappings/index.html",
    "mappings/rag-pipeline/index.html",
    "mappings/hem-dio/index.html",
    "mappings/commit-boundary-policy/index.html",
    "mappings/agentic-er-architecture/index.html",
    "metadata/index.html",
    "semantic-change-feed/index.html",
)


def blocks(path: Path):
    html = path.read_text(encoding="utf-8")
    return [
        json.loads(match.group(1))
        for match in re.finditer(
            r'<script type="application/ld\+json">([\s\S]*?)</script>', html
        )
    ]


def all_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from all_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_nodes(child)


def verify_person_nodes(documents, source_label: str):
    found = 0
    for document in documents:
        for node in all_nodes(document):
            node_type = node.get("@type")
            is_person = node_type == "Person" or (
                isinstance(node_type, list) and "Person" in node_type
            )
            if is_person and node.get("@id") == PERSON_ID:
                found += 1
                if node.get("name") != PERSON["name"]:
                    raise SystemExit(f"{source_label}: full Person name differs from Entity Registry.")
                if node.get("url") != PROFILE_URL:
                    raise SystemExit(f"{source_label}: full Person URL differs from canonical biography.")
                if node.get("sameAs") != PERSON.get("sameAs", []):
                    raise SystemExit(f"{source_label}: full Person sameAs differs from Entity Registry.")
    return found


home_blocks = blocks(ROOT / "index.html")
if not home_blocks:
    raise SystemExit("Missing Reference Model homepage JSON-LD.")
home = next(
    (block for block in home_blocks if isinstance(block, dict) and isinstance(block.get("@graph"), list)),
    None,
)
if not home:
    raise SystemExit("Reference Model homepage must publish an @graph.")
home_nodes = {
    node.get("@id"): node
    for node in home["@graph"]
    if isinstance(node, dict) and node.get("@id")
}
if len(home_nodes) != len(home["@graph"]):
    raise SystemExit("Reference Model homepage graph must use unique @id values.")
person = home_nodes.get(PERSON_ID)
if (
    not person
    or person.get("name") != PERSON["name"]
    or person.get("url") != PROFILE_URL
    or person.get("sameAs") != PERSON.get("sameAs", [])
):
    raise SystemExit("Reference Model Person must match the canonical Entity Registry identity.")
page = home_nodes.get(ROOT_PAGE)
if not page or page.get("@type") != "CollectionPage" or page.get("mainEntity", {}).get("@id") != MODEL_ID:
    raise SystemExit("Reference Model homepage must identify the Reference Model as its main entity.")
model = home_nodes.get(MODEL_ID)
if not model or model.get("@type") != "CreativeWork" or model.get("mainEntityOfPage", {}).get("@id") != ROOT_PAGE:
    raise SystemExit("Reference Model CreativeWork → CollectionPage relation is missing.")
if VOCAB_ID not in [item.get("@id") for item in model.get("hasPart", [])]:
    raise SystemExit("Reference Model must link its canonical Reference Vocabulary.")

vocab_blocks = blocks(ROOT / "dio-odi/index.html")
if len(vocab_blocks) < 2:
    raise SystemExit("Missing vocabulary or Dataset JSON-LD.")
vocab_graph = next(
    (block.get("@graph") for block in vocab_blocks if isinstance(block, dict) and isinstance(block.get("@graph"), list)),
    None,
)
if not vocab_graph:
    raise SystemExit("Vocabulary page must identify its WebPage and DefinedTermSet in an @graph.")
vocab_nodes = {
    node.get("@id"): node
    for node in vocab_graph
    if isinstance(node, dict) and node.get("@id")
}
if len(vocab_nodes) != len(vocab_graph):
    raise SystemExit("Vocabulary graph must use unique @id values.")
webpage = vocab_nodes.get(VOCAB_PAGE)
termset = vocab_nodes.get(VOCAB_ID)
if not webpage or webpage.get("mainEntity", {}).get("@id") != VOCAB_ID:
    raise SystemExit("Vocabulary WebPage → DefinedTermSet relationship is missing.")
if not termset or termset.get("mainEntityOfPage", {}).get("@id") != VOCAB_PAGE:
    raise SystemExit("DefinedTermSet → vocabulary WebPage relationship is missing.")
dataset = next(
    (block for block in vocab_blocks if isinstance(block, dict) and block.get("@type") == "Dataset"),
    None,
)
if not dataset or dataset.get("mainEntityOfPage", {}).get("@id") != VOCAB_PAGE:
    raise SystemExit("Vocabulary Dataset → vocabulary WebPage relationship is missing.")

total_person_nodes = 0
for relative_path in PERSON_SURFACES:
    documents = blocks(ROOT / relative_path)
    count = verify_person_nodes(documents, relative_path)
    if count == 0:
        raise SystemExit(f"{relative_path}: expected a full canonical Person node.")
    total_person_nodes += count

for relative_path in PERSON_SURFACES:
    for document in blocks(ROOT / relative_path):
        for node in all_nodes(document):
            if node.get("@type") == "LocalBusiness" or any(
                key in node for key in ("address", "geo", "openingHours", "areaServed", "makesOffer")
            ):
                raise SystemExit("Local-business details must not be propagated to the Reference Model subdomain.")

print(
    "Reference Model JSON-LD is valid against Entity Registry "
    f"v{REGISTRY['registry_version']}: {total_person_nodes} full Person projections, "
    "CollectionPage, Reference Model, DefinedTermSet and Dataset relations."
)
