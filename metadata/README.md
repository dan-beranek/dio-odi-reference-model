# DIO/ODI metadata registry

This directory is the operational metadata source of truth for the DIO/ODI publication corpus and the DIO/ODI Reference Model.

It is deliberately separate from the canonical DIO/ODI Reference Vocabulary. Updating these files does not modify vocabulary definitions, hierarchy, or concept provenance.

## Files

- `works.json` — identities and publication metadata of DIO/ODI works and Reference Model releases.
- `relations.json` — directed inter-work relation graph. Only relations with `approved_for_zenodo: true` should be projected automatically into Zenodo metadata.
- `references.json` — canonical bibliographic strings for internal and external references.
- root `.zenodo.json` — Zenodo-specific projection for future GitHub → Zenodo Reference Model releases.

## Workflow

1. Maintain work identities, DOI/version information, relations, and citations here.
2. Before a new Reference Model release, ensure `.zenodo.json` reflects the approved subset of this registry.
3. Zenodo GitHub archiving reads `.zenodo.json` for new releases.
4. Existing historical Zenodo records are not retroactively changed by these files; they require a one-time metadata synchronization through Zenodo's editor, API, or browser automation.

## Relation discipline

The graph is intentionally conservative. A relation should not be strengthened merely to make the graph denser.

In particular, the candidate relation between the archived Reference Model package and the namespace URI `https://vocab.danielberanek.cz/dio-odi/#` is currently marked for semantic review rather than exported automatically as `isIdenticalTo`.
