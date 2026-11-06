#!/usr/bin/env python3
"""Verify published DIO/ODI endpoints and their HTTP media types.

This complements the repository-local integrity checks: it tests the deployed
public site rather than assuming that valid source files are served correctly.
"""
from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

BASE_URL = "https://vocab.danielberanek.cz"
SITEMAP = Path(__file__).resolve().parents[1] / "sitemap.xml"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

ACCEPTED_MEDIA_TYPES = {
    ".html": {"text/html"},
    ".md": {"text/markdown", "text/plain"},
    ".ttl": {"text/turtle", "application/x-turtle", "text/plain"},
    ".jsonld": {"application/ld+json", "application/json"},
    ".json": {"application/json"},
    ".svg": {"image/svg+xml"},
    ".xml": {"application/xml", "text/xml"},
    ".txt": {"text/plain", "text/markdown"},
    ".sparql": {"application/sparql-query", "text/plain"},
}
GENERIC_MEDIA_TYPES = {
    ".ttl": {"text/plain"},
    ".sparql": {"text/plain"},
}
EXTRA_ENDPOINTS = (
    f"{BASE_URL}/llms.txt",
    f"{BASE_URL}/metadata.json",
)


def discover_urls() -> list[str]:
    try:
        root = ET.parse(SITEMAP).getroot()
    except (OSError, ET.ParseError) as exc:
        raise RuntimeError(f"Cannot parse sitemap.xml: {exc}") from exc

    urls = {
        node.findtext("sm:loc", namespaces=SITEMAP_NS)
        for node in root.findall(".//sm:url", SITEMAP_NS)
    }
    urls.update(EXTRA_ENDPOINTS)
    urls.discard(None)
    return sorted(urls)


def expected_types(url: str) -> set[str]:
    path = urlparse(url).path
    if path.endswith("/"):
        return {"text/html"}
    suffix = Path(path).suffix.lower()
    if suffix not in ACCEPTED_MEDIA_TYPES:
        raise RuntimeError(f"No MIME expectation is defined for {url}")
    return ACCEPTED_MEDIA_TYPES[suffix]


def request_headers(url: str) -> tuple[int, str, str]:
    headers = {
        "User-Agent": "DIO-ODI-Reference-Model-public-endpoint-check/1.0",
        "Accept": "*/*",
    }
    request = urllib.request.Request(url, headers=headers, method="HEAD")
    try:
        response = urllib.request.urlopen(request, timeout=20)
    except urllib.error.HTTPError as exc:
        if exc.code not in (403, 405, 501):
            raise
        # Some static hosts or edge rules do not implement HEAD consistently.
        headers["Range"] = "bytes=0-0"
        request = urllib.request.Request(url, headers=headers, method="GET")
        response = urllib.request.urlopen(request, timeout=20)

    with response:
        status = response.status
        media_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        final_url = response.geturl()
    return status, media_type, final_url


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    urls = discover_urls()

    for url in urls:
        try:
            status, media_type, final_url = request_headers(url)
            accepted = expected_types(url)
            if not 200 <= status < 400:
                failures.append(f"{url}: unexpected HTTP status {status}")
                continue
            if media_type not in accepted:
                failures.append(
                    f"{url}: Content-Type {media_type!r}; expected one of {sorted(accepted)}"
                )
                continue
            suffix = Path(urlparse(url).path).suffix.lower()
            if media_type in GENERIC_MEDIA_TYPES.get(suffix, set()):
                warnings.append(
                    f"{url}: served as generic {media_type}; a format-specific MIME type is preferable"
                )
            print(f"PASS {status} {media_type} {url}")
            if final_url != url:
                print(f"     redirected to {final_url}")
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            failures.append(f"{url}: {exc}")
        except Exception as exc:  # keep the audit fail-closed for unexpected response errors
            failures.append(f"{url}: unexpected check error: {type(exc).__name__}: {exc}")
        time.sleep(0.05)

    print(f"Checked {len(urls)} public endpoints.")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Public endpoint and MIME-type validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
