#!/usr/bin/env python3
"""Generate page-level SEO and Schema.org metadata from canonical DIO/ODI surface profiles.

The keyword registry remains the sole source of C0-C6 terms and selectors. This
script only projects approved profiles onto the public HTML pages owned by this
repository; it does not modify publication work_profiles or source JSON-LD
entities other than adding a linked keyword-property node.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = "metadata/keywords.json"
MANIFEST_PATH = "assets/data/resolved-page-metadata.json"
SITEMAP_PATH = "sitemap.xml"
REPOSITORY = "dan-beranek/dio-odi-reference-model"
SITE_ORIGIN = "https://vocab.danielberanek.cz"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
CHUNK_ORDER = [
    "C0_identity_invariant",
    "C1_reconstruction_environments",
    "C2_work_positioning",
    "C3_reconstruction_mechanics",
    "C4_k6",
    "C5_failures_robustness",
    "C6_machine_readable_representation",
]
GENERATED_SCRIPT_ATTR = 'data-dio-odi-keyword-surface="true"'


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"Required file is missing: {relative}")
    return path.read_text(encoding="utf-8")


def write_text(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def resolve_keywords(registry: dict, profile_id: str, profile: dict) -> tuple[list[str], dict[str, list[str]]]:
    if profile.get("status") != "canonical-approved":
        raise ValueError(f"{profile_id}: surface profile is not canonical-approved")
    if profile.get("scope") != "derived-public-webpage":
        raise ValueError(f"{profile_id}: expected scope derived-public-webpage")

    chunks = registry.get("chunks", {})
    selectors = profile.get("chunks", {})
    if selectors.get("C0_identity_invariant") != "all":
        raise ValueError(f"{profile_id}: C0 must always be exported in full")
    if not isinstance(selectors.get("C1_reconstruction_environments"), list):
        raise ValueError(f"{profile_id}: C1 must be an explicit ordered selection")
    if selectors.get("C4_k6") not in ("all", "none"):
        raise ValueError(f"{profile_id}: K6 must be complete or absent")
    if set(selectors) != set(CHUNK_ORDER):
        raise ValueError(f"{profile_id}: chunk selectors must match the canonical C0-C6 set")

    resolved: list[str] = []
    resolved_chunks: dict[str, list[str]] = {}
    seen: set[str] = set()
    for chunk_name in CHUNK_ORDER:
        source_terms = chunks.get(chunk_name, {}).get("terms")
        if not isinstance(source_terms, list):
            raise ValueError(f"{profile_id}: canonical chunk {chunk_name} has no terms")
        selector = selectors[chunk_name]
        if selector == "all":
            selected = list(source_terms)
        elif selector == "none":
            selected = []
        elif isinstance(selector, list):
            selected = selector
            if chunk_name != "C2_work_positioning":
                positions = [source_terms.index(term) if term in source_terms else -1 for term in selected]
                if -1 in positions or positions != sorted(positions) or len(set(selected)) != len(selected):
                    raise ValueError(f"{profile_id}: {chunk_name} must preserve canonical order and uniqueness")
            elif len({term.casefold() for term in selected}) != len(selected):
                raise ValueError(f"{profile_id}: duplicate terms in C2_work_positioning")
        else:
            raise ValueError(f"{profile_id}: invalid selector for {chunk_name}")

        resolved_chunks[chunk_name] = selected
        for term in selected:
            folded = term.casefold()
            if folded not in seen:
                seen.add(folded)
                resolved.append(term)

    c0 = set(chunks["C0_identity_invariant"]["terms"])
    required_rationales = set(resolved) - c0
    rationales = profile.get("term_rationales", {})
    if set(rationales) != required_rationales or any(not str(rationales.get(term, "")).strip() for term in required_rationales):
        missing = sorted(required_rationales - set(rationales))
        extra = sorted(set(rationales) - required_rationales)
        raise ValueError(f"{profile_id}: rationale coverage mismatch; missing={missing}; extra={extra}")
    if len(resolved) != len({term.casefold() for term in resolved}):
        raise ValueError(f"{profile_id}: duplicate terms in resolved sequence")
    return resolved, resolved_chunks


def candidate_nodes(document):
    """Yield primary JSON-LD graph nodes, not nested hasPart/author entities."""
    if isinstance(document, list):
        for item in document:
            yield from candidate_nodes(item)
    elif isinstance(document, dict):
        graph = document.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict):
                    yield item
        elif "url" in document or "@id" in document:
            yield document


def schema_type_names(node: dict) -> set[str]:
    value = node.get("@type", [])
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    return set()


def find_page_entity(html_text: str, page_url: str, profile_id: str) -> str:
    script_pattern = re.compile(
        r"<script\b(?=[^>]*\btype\s*=\s*([\"'])application/ld\+json\1)[^>]*>([\s\S]*?)</script\s*>",
        re.IGNORECASE,
    )
    candidates: list[dict] = []
    for match in script_pattern.finditer(html_text):
        try:
            document = json.loads(match.group(2).strip())
        except json.JSONDecodeError as exc:
            raise ValueError(f"{profile_id}: malformed existing JSON-LD: {exc}") from exc
        for node in candidate_nodes(document):
            if node.get("url") == page_url and isinstance(node.get("@id"), str):
                candidates.append(node)

    if not candidates:
        raise ValueError(f"{profile_id}: no primary JSON-LD node with url {page_url!r} and @id was found")

    priorities = {
        "CollectionPage": 0,
        "WebPage": 0,
        "DefinedTermSet": 1,
        "TechArticle": 2,
        "Dataset": 3,
        "CreativeWork": 4,
        "WebSite": 9,
    }
    candidates.sort(key=lambda node: min((priorities.get(item, 5) for item in schema_type_names(node)), default=5))
    best_priority = min((priorities.get(item, 5) for item in schema_type_names(candidates[0])), default=5)
    best = [node for node in candidates if min((priorities.get(item, 5) for item in schema_type_names(node)), default=5) == best_priority]
    if len({node["@id"] for node in best}) != 1:
        raise ValueError(f"{profile_id}: ambiguous primary JSON-LD page entities for {page_url!r}")
    return best[0]["@id"]


def upsert_meta(html_text: str, name: str, value: str, profile_id: str) -> str:
    escaped_name = re.escape(name)
    pattern = re.compile(
        rf"<meta\b(?=[^>]*\bname\s*=\s*([\"']){escaped_name}\1)[^>]*>",
        re.IGNORECASE,
    )
    tag = f'<meta name="{html.escape(name, quote=True)}" content="{html.escape(value, quote=True)}">'
    matches = list(pattern.finditer(html_text))
    if len(matches) > 1:
        raise ValueError(f"{profile_id}: duplicate meta name={name!r} elements")
    if matches:
        match = matches[0]
        return html_text[:match.start()] + tag + html_text[match.end():]

    description_pattern = re.compile(
        r"<meta\b(?=[^>]*\bname\s*=\s*([\"'])description\1)[^>]*>",
        re.IGNORECASE,
    )
    descriptions = list(description_pattern.finditer(html_text))
    if len(descriptions) != 1:
        raise ValueError(f"{profile_id}: expected exactly one meta description to anchor {name!r}")
    anchor = descriptions[0]
    return html_text[:anchor.end()] + "\n" + tag + html_text[anchor.end():]


def upsert_jsonld_keyword_node(html_text: str, page_entity_id: str, keywords: list[str], profile_id: str) -> str:
    script_pattern = re.compile(
        r"<script\b(?=[^>]*\bdata-dio-odi-keyword-surface\s*=\s*([\"'])true\1)[^>]*>[\s\S]*?</script\s*>",
        re.IGNORECASE,
    )
    node = {
        "@context": "https://schema.org",
        "@id": page_entity_id,
        "keywords": keywords,
    }
    payload = json.dumps(node, ensure_ascii=False, separators=(",", ":"))
    tag = (
        '<script type="application/ld+json" data-dio-odi-keyword-surface="true">'
        + payload
        + "</script>"
    )
    matches = list(script_pattern.finditer(html_text))
    if len(matches) > 1:
        raise ValueError(f"{profile_id}: more than one generated keyword JSON-LD node exists")
    if matches:
        match = matches[0]
        return html_text[:match.start()] + tag + html_text[match.end():]

    head_end = re.search(r"</head\s*>", html_text, re.IGNORECASE)
    if not head_end:
        raise ValueError(f"{profile_id}: closing </head> not found")
    return html_text[:head_end.start()] + tag + "\n" + html_text[head_end.start():]


def registry_change_date() -> date:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", REGISTRY_PATH],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return datetime.fromisoformat(result.stdout.strip()).astimezone(timezone.utc).date()
    return date.today()


def update_sitemap(source: str, pages: list[dict], manifest_url: str, modified: date) -> str:
    ET.register_namespace("", SITEMAP_NS)
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid sitemap XML: {exc}") from exc
    if not root.tag.endswith("urlset"):
        raise ValueError("sitemap.xml does not have a urlset root")

    url_tag = f"{{{SITEMAP_NS}}}url"
    loc_tag = f"{{{SITEMAP_NS}}}loc"
    lastmod_tag = f"{{{SITEMAP_NS}}}lastmod"
    by_url = {}
    for node in root.findall(url_tag):
        loc = node.findtext(loc_tag)
        if loc:
            by_url[loc] = node

    targets = [(page["url"], page["path"]) for page in pages]
    targets.append((manifest_url, MANIFEST_PATH))
    for url, _path in targets:
        node = by_url.get(url)
        if node is None:
            node = ET.SubElement(root, url_tag)
            ET.SubElement(node, loc_tag).text = url
            ET.SubElement(node, lastmod_tag).text = modified.isoformat()
            by_url[url] = node
            continue
        lastmod = node.find(lastmod_tag)
        if lastmod is None:
            lastmod = ET.SubElement(node, lastmod_tag)
        try:
            existing = date.fromisoformat(lastmod.text or "")
        except ValueError:
            existing = date.min
        lastmod.text = max(existing, modified).isoformat()

    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def build_outputs() -> dict[str, str]:
    registry_text = read_text(REGISTRY_PATH)
    registry = json.loads(registry_text)
    if registry.get("status") != "canonical-approved":
        raise ValueError("The canonical keyword registry is not approved")
    version = registry.get("registry_version", "")
    if not re.fullmatch(r"2\.\d+\.\d+", version):
        raise ValueError(f"Unsupported keyword registry version: {version!r}")

    selected_profiles = []
    profile_index = registry.get("surface_profiles", {})
    for profile_id, profile in profile_index.items():
        surface = profile.get("surface", {})
        if surface.get("repository") != REPOSITORY:
            continue
        if profile.get("status") != "canonical-approved":
            raise ValueError(f"{profile_id}: repository surface profile is not approved")
        paths = surface.get("paths")
        urls = surface.get("urls")
        if not isinstance(paths, list) or len(paths) != 1 or not isinstance(urls, list) or len(urls) != 1:
            raise ValueError(f"{profile_id}: Reference Model pages require exactly one path and one canonical URL")
        page_path = paths[0]
        page_url = urls[0]
        if not isinstance(page_path, str) or not isinstance(page_url, str):
            raise ValueError(f"{profile_id}: path and URL must be strings")
        parsed = urlparse(page_url)
        if parsed.scheme != "https" or parsed.netloc != "vocab.danielberanek.cz":
            raise ValueError(f"{profile_id}: page URL is outside the canonical site origin")
        if not (ROOT / page_path).is_file():
            raise ValueError(f"{profile_id}: mapped HTML page does not exist: {page_path}")
        keywords, chunks = resolve_keywords(registry, profile_id, profile)
        selected_profiles.append({
            "id": profile_id,
            "page_key": surface.get("page_key"),
            "path": page_path,
            "url": page_url,
            "purpose": profile.get("purpose", ""),
            "scope": profile.get("scope"),
            "keyword_chunks": chunks,
            "keywords": keywords,
            "keyword_rationales": profile.get("term_rationales", {}),
            "profile_status": profile.get("status"),
        })

    selected_profiles.sort(key=lambda item: item["url"])
    if len(selected_profiles) != 10:
        raise ValueError(f"Expected exactly 10 Reference Model page profiles; found {len(selected_profiles)}")
    if len({item["page_key"] for item in selected_profiles}) != len(selected_profiles):
        raise ValueError("Duplicate Reference Model page_key in canonical surface profiles")
    if len({item["url"] for item in selected_profiles}) != len(selected_profiles):
        raise ValueError("Duplicate Reference Model page URL in canonical surface profiles")

    sha256 = hashlib.sha256(registry_text.encode("utf-8")).hexdigest()
    modified = registry_change_date()
    outputs: dict[str, str] = {}
    manifest_pages = []

    for artifact in selected_profiles:
        html_text = read_text(artifact["path"])
        page_entity_id = find_page_entity(html_text, artifact["url"], artifact["id"])
        profile_id = artifact["id"]
        html_text = upsert_meta(html_text, "keywords", ", ".join(artifact["keywords"]), profile_id)
        html_text = upsert_meta(html_text, "dio-odi:keyword-profile", profile_id, profile_id)
        html_text = upsert_meta(html_text, "dio-odi:keyword-registry-version", version, profile_id)
        html_text = upsert_jsonld_keyword_node(html_text, page_entity_id, artifact["keywords"], profile_id)
        outputs[artifact["path"]] = html_text
        manifest_pages.append({
            **artifact,
            "schema_entity_id": page_entity_id,
            "in_language": "en",
        })

    manifest = {
        "schema_version": "1.0.0",
        "site": {
            "id": SITE_ORIGIN + "/#website",
            "url": SITE_ORIGIN + "/",
            "name": "DIO/ODI Reference Model",
            "repository": REPOSITORY,
        },
        "keyword_registry": {
            "repository": REPOSITORY,
            "file": REGISTRY_PATH,
            "registry_version": version,
            "status": registry["status"],
            "sha256": sha256,
        },
        "artifacts": manifest_pages,
    }
    outputs[MANIFEST_PATH] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    outputs[SITEMAP_PATH] = update_sitemap(
        read_text(SITEMAP_PATH),
        manifest_pages,
        SITE_ORIGIN + "/" + MANIFEST_PATH,
        modified,
    )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail if generated page metadata is stale; do not write files.")
    mode.add_argument("--write", action="store_true", help="Write generated page metadata (the default).")
    args = parser.parse_args()

    try:
        outputs = build_outputs()
        stale = []
        for relative, content in outputs.items():
            path = ROOT / relative
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current != content:
                stale.append(relative)
                if not args.check:
                    write_text(relative, content)
        if args.check and stale:
            print("Generated page metadata is stale:", file=sys.stderr)
            for relative in stale:
                print(f"- {relative}", file=sys.stderr)
            return 1
        if args.check:
            print("Page-level metadata is reproducible.")
        else:
            print(f"Generated page-level metadata for {len(json.loads(outputs[MANIFEST_PATH])['artifacts'])} Reference Model pages.")
            if stale:
                print("Updated:")
                for relative in stale:
                    print(f"- {relative}")
        return 0
    except Exception as exc:
        print(f"PAGE METADATA GENERATION FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
