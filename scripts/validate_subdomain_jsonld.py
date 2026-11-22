#!/usr/bin/env python3
"""Validate the Reference Model subdomain's canonical JSON-LD relationships."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSON_ID = "https://danielberanek.cz/#person"
PROFILE_URL = "https://danielberanek.cz/od-pultu-az-k-seo-a-copy-s-ostrymi-hroty-profesni-bio/"
PROFILE_ID = PROFILE_URL + "#profilepage"
ROOT_URL = "https://vocab.danielberanek.cz/"
ROOT_PAGE = ROOT_URL + "#webpage"
MODEL_ID = ROOT_URL + "#reference-model"
VOCAB_URL = ROOT_URL + "dio-odi/"
VOCAB_PAGE = VOCAB_URL + "#webpage"
VOCAB_ID = VOCAB_URL + "#ReferenceVocabulary"

def blocks(path: Path):
    html = path.read_text(encoding="utf-8")
    return [json.loads(m.group(1)) for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', html)]

def all_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from all_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_nodes(child)

def verify_person_nodes(documents):
    for document in documents:
        for node in all_nodes(document):
            if node.get("@type") == "Person" and node.get("@id") == PERSON_ID and "name" in node:
                if node.get("mainEntityOfPage", {}).get("@id") != PROFILE_ID:
                    raise SystemExit("A full Person node is missing the canonical ProfilePage relation.")
                if node.get("url") != PROFILE_URL:
                    raise SystemExit("A full Person node must use the canonical biography URL.")

home_blocks = blocks(ROOT / "index.html")
if not home_blocks:
    raise SystemExit("Missing Reference Model homepage JSON-LD.")
home = next((b for b in home_blocks if isinstance(b, dict) and isinstance(b.get("@graph"), list)), None)
if not home:
    raise SystemExit("Reference Model homepage must publish an @graph.")
home_nodes = {n.get("@id"):n for n in home["@graph"] if isinstance(n,dict) and n.get("@id")}
if len(home_nodes) != len(home["@graph"]):
    raise SystemExit("Reference Model homepage graph must use unique @id values.")
person = home_nodes.get(PERSON_ID)
if not person or person.get("mainEntityOfPage", {}).get("@id") != PROFILE_ID:
    raise SystemExit("Reference Model Person → ProfilePage relation is missing.")
page = home_nodes.get(ROOT_PAGE)
if not page or page.get("@type") != "CollectionPage" or page.get("mainEntity",{}).get("@id") != MODEL_ID:
    raise SystemExit("Reference Model homepage must identify the Reference Model as its main entity.")
model = home_nodes.get(MODEL_ID)
if not model or model.get("@type") != "CreativeWork" or model.get("mainEntityOfPage",{}).get("@id") != ROOT_PAGE:
    raise SystemExit("Reference Model CreativeWork → CollectionPage relation is missing.")
if VOCAB_ID not in [item.get("@id") for item in model.get("hasPart",[])]:
    raise SystemExit("Reference Model must link its canonical Reference Vocabulary.")

vocab_blocks = blocks(ROOT / "dio-odi/index.html")
if len(vocab_blocks) < 2:
    raise SystemExit("Missing vocabulary or Dataset JSON-LD.")
vocab_graph = next((b.get("@graph") for b in vocab_blocks if isinstance(b,dict) and isinstance(b.get("@graph"),list)), None)
if not vocab_graph:
    raise SystemExit("Vocabulary page must identify its WebPage and DefinedTermSet in an @graph.")
vocab_nodes = {n.get("@id"):n for n in vocab_graph if isinstance(n,dict) and n.get("@id")}
if len(vocab_nodes) != len(vocab_graph):
    raise SystemExit("Vocabulary graph must use unique @id values.")
webpage = vocab_nodes.get(VOCAB_PAGE)
termset = vocab_nodes.get(VOCAB_ID)
if not webpage or webpage.get("mainEntity",{}).get("@id") != VOCAB_ID:
    raise SystemExit("Vocabulary WebPage → DefinedTermSet relationship is missing.")
if not termset or termset.get("mainEntityOfPage",{}).get("@id") != VOCAB_PAGE:
    raise SystemExit("DefinedTermSet → vocabulary WebPage relationship is missing.")
dataset = next((b for b in vocab_blocks if isinstance(b,dict) and b.get("@type") == "Dataset"), None)
if not dataset or dataset.get("mainEntityOfPage",{}).get("@id") != VOCAB_PAGE:
    raise SystemExit("Vocabulary Dataset → vocabulary WebPage relationship is missing.")
verify_person_nodes(home_blocks + vocab_blocks)
for document in home_blocks + vocab_blocks:
    for node in all_nodes(document):
        if node.get("@type") == "LocalBusiness" or any(k in node for k in ("address","geo","openingHours","areaServed","makesOffer")):
            raise SystemExit("Local-business details must not be propagated to the Reference Model subdomain.")
print("Reference Model JSON-LD is valid: canonical Person, CollectionPage, Reference Model, DefinedTermSet and Dataset relations.")
