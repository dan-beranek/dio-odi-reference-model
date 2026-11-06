import { McpServer, ResourceTemplate } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';
import { extractConcepts, resolveConcept, searchConcepts, type ConceptSummary, type JsonObject } from './catalog.js';
import { loadData, loadMapping, type DataSourceOptions } from './data.js';

const SERVER_VERSION = '0.1.0';
const MAPPING_PATHS: Record<string, string> = {
  'rag-pipeline': 'mappings/rag-pipeline-mapping.md',
  'hem-dio': 'mappings/hem-dio-mapping.md',
  'commit-boundary-policy': 'mappings/commit-boundary-policy-mapping.md',
  'agentic-er-architecture': 'mappings/agentic-er-commit-boundary-architecture-mapping.md'
};

function jsonText(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function sourceContext(metadata: JsonObject, sourceRef: string, releaseTag: string): JsonObject {
  const release = metadata.current_release as JsonObject;
  return {
    reference_model: metadata.title,
    version: metadata.version,
    doi: release.doi,
    doi_url: release.doi_url,
    reference_vocabulary_version: metadata.reference_vocabulary_version,
    source_repository: metadata.repository,
    source_ref: sourceRef,
    source_release_tag: releaseTag,
    license: metadata.license,
    attribution: 'Daniel Beránek, DIO/ODI Reference Model; CC BY 4.0.'
  };
}

function mappingSummaries(metadata: JsonObject): JsonObject[] {
  const mappings = Array.isArray(metadata.derived_application_mappings)
    ? metadata.derived_application_mappings as JsonObject[]
    : [];
  return mappings.map((mapping) => {
    const path = String(mapping.path ?? '');
    const id = Object.entries(MAPPING_PATHS).find((entry) => entry[1] === path)?.[0] ?? path;
    return {
      id,
      title: mapping.title,
      relation: mapping.relation,
      introduced_in: mapping.introduced_in,
      mapping_version: mapping.mapping_version,
      release_status: mapping.release_status,
      archived_release_doi: mapping.archived_release_doi,
      frontend: mapping.frontend,
      source_markdown: path,
      machine_readable_metadata: mapping.machine_readable_metadata,
      turtle_rdf: mapping.turtle_rdf
    };
  });
}

function publicationSummary(work: JsonObject): JsonObject {
  const identifiers: string[] = [];
  for (const key of ['concept_doi', 'version_doi', 'current_version_doi', 'preferred_relation_identifier']) {
    if (typeof work[key] === 'string') identifiers.push(work[key] as string);
  }
  const addDoi = (value: unknown) => {
    if (value && typeof value === 'object' && typeof (value as JsonObject).doi === 'string') {
      identifiers.push((value as JsonObject).doi as string);
    }
  };
  addDoi(work.current_release);
  for (const value of Array.isArray(work.releases) ? work.releases : []) addDoi(value);
  for (const value of Array.isArray(work.versions) ? work.versions : []) addDoi(value);
  const currentRelease = work.current_release && typeof work.current_release === 'object'
    ? work.current_release as JsonObject
    : undefined;
  return {
    id: work.id,
    title: work.title,
    type: work.type,
    current_version: work.current_version ?? currentRelease?.version,
    identifiers: [...new Set(identifiers)],
    canonical_url: work.canonical_url,
    repository: work.repository,
    license: work.license
  };
}

function conceptResponse(concept: ConceptSummary, all: ConceptSummary[]): JsonObject {
  const byUri = new Map(all.map((item) => [item.uri, item]));
  const labels = (items: typeof concept.prefLabels) =>
    items.map((item) => ({ value: item.value, language: item.language ?? null }));
  const relationDetails = (uris: string[]) => uris.map((uri) => {
    const target = byUri.get(uri);
    return target
      ? { uri, id: target.id, pref_labels: labels(target.prefLabels) }
      : { uri, id: uri };
  });
  return {
    id: concept.id,
    uri: concept.uri,
    pref_labels: labels(concept.prefLabels),
    alt_labels: labels(concept.altLabels),
    definitions: labels(concept.definitions),
    scope_notes: labels(concept.scopeNotes),
    examples: labels(concept.examples),
    broader: relationDetails(concept.broader),
    narrower: relationDetails(concept.narrower),
    related: relationDetails(concept.related),
    has_part: relationDetails(concept.hasPart),
    is_part_of: relationDetails(concept.isPartOf),
    sources: concept.sources
  };
}

function errorResult(error: unknown) {
  return {
    content: [{ type: 'text' as const, text: error instanceof Error ? error.message : String(error) }],
    isError: true
  };
}

export function createDioOdiServer(sourceOptions: DataSourceOptions = {}): McpServer {
  const server = new McpServer({ name: 'dio-odi-reference-model', version: SERVER_VERSION });

  server.registerTool(
    'get_reference_model_info',
    {
      description: 'Return the current archived DIO/ODI Reference Model release, canonical DOI, vocabulary version, source ref and licence. Read-only.',
      
    },
    async () => {
      try {
        const data = await loadData(sourceOptions);
        return {
          content: [{
            type: 'text',
            text: jsonText({
              ...sourceContext(data.metadata, data.sourceRef, data.releaseTag),
              archive_status: data.metadata.status
            })
          }]
        };
      } catch (error) { return errorResult(error); }
    }
  );

  server.registerTool(
    'search_concepts',
    {
      description: 'Search the canonical SKOS Reference Vocabulary by concept identifier, preferred label, alternative label, definition or scope note. Returns exact/substring matches only; it does not invent concepts or perform semantic inference.',
      inputSchema: {
        query: z.string().min(1).max(200).describe('Search phrase, concept label, acronym, local ID, or canonical URI.'),
        limit: z.number().int().min(1).max(50).default(10).describe('Maximum number of concepts to return.')
      }
    },
    async ({ query, limit }) => {
      try {
        const data = await loadData(sourceOptions);
        const results = searchConcepts(data.vocabularyJsonLd, query, limit);
        const all = extractConcepts(data.vocabularyJsonLd);
        return {
          content: [{
            type: 'text',
            text: jsonText({
              query,
              total_returned: results.length,
              results: results.map((item) => conceptResponse(item, all)),
              source: sourceContext(data.metadata, data.sourceRef, data.releaseTag)
            })
          }]
        };
      } catch (error) { return errorResult(error); }
    }
  );

  server.registerTool(
    'get_concept',
    {
      description: 'Retrieve one canonical SKOS concept by full URI, dio: prefixed ID, local ID, preferred label or alternative label. Ambiguous labels are reported rather than guessed.',
      inputSchema: {
        identifier: z.string().min(1).max(500).describe('For example: DIO, dio:K6, or the full canonical concept URI.')
      }
    },
    async ({ identifier }) => {
      try {
        const data = await loadData(sourceOptions);
        const matches = resolveConcept(data.vocabularyJsonLd, identifier);
        if (matches.length === 0) {
          return { content: [{ type: 'text', text: 'No exact concept match for: ' + identifier }], isError: true };
        }
        if (matches.length > 1) {
          return {
            content: [{
              type: 'text',
              text: jsonText({
                ambiguous: true,
                identifier,
                candidates: matches.map((item) => ({
                  id: item.id,
                  uri: item.uri,
                  pref_labels: item.prefLabels
                }))
              })
            }]
          };
        }
        const all = extractConcepts(data.vocabularyJsonLd);
        return {
          content: [{
            type: 'text',
            text: jsonText({
              concept: conceptResponse(matches[0]!, all),
              source: sourceContext(data.metadata, data.sourceRef, data.releaseTag)
            })
          }]
        };
      } catch (error) { return errorResult(error); }
    }
  );

  server.registerTool(
    'list_concepts',
    {
      description: 'List canonical SKOS concepts in stable identifier order. Use offset and limit for pagination.',
      inputSchema: {
        offset: z.number().int().min(0).max(1000).default(0),
        limit: z.number().int().min(1).max(50).default(20)
      }
    },
    async ({ offset, limit }) => {
      try {
        const data = await loadData(sourceOptions);
        const concepts = extractConcepts(data.vocabularyJsonLd);
        const page = concepts.slice(offset, offset + limit);
        return {
          content: [{
            type: 'text',
            text: jsonText({
              total_concepts: concepts.length,
              offset,
              limit,
              results: page.map((item) => ({
                id: item.id,
                uri: item.uri,
                pref_labels: item.prefLabels,
                definitions: item.definitions
              })),
              source: sourceContext(data.metadata, data.sourceRef, data.releaseTag)
            })
          }]
        };
      } catch (error) { return errorResult(error); }
    }
  );

  server.registerTool(
    'list_application_mappings',
    {
      description: 'List derived DIO/ODI application mappings. They are separate from, and do not modify, the canonical Reference Vocabulary.',
      inputSchema: z.object({})
    },
    async () => {
      try {
        const data = await loadData(sourceOptions);
        return {
          content: [{
            type: 'text',
            text: jsonText({
              mappings: mappingSummaries(data.metadata),
              source: sourceContext(data.metadata, data.sourceRef, data.releaseTag)
            })
          }]
        };
      } catch (error) { return errorResult(error); }
    }
  );

  server.registerTool(
    'get_application_mapping',
    {
      description: 'Retrieve the full Markdown source of one published derived application mapping by ID: rag-pipeline, hem-dio, commit-boundary-policy, or agentic-er-architecture.',
      inputSchema: { mapping_id: z.enum(['rag-pipeline', 'hem-dio', 'commit-boundary-policy', 'agentic-er-architecture']) }
    },
    async ({ mapping_id }) => {
      try {
        const data = await loadData(sourceOptions);
        const path = MAPPING_PATHS[mapping_id];
        if (!path) return errorResult(new Error('Unknown application mapping ID: ' + mapping_id));
        const markdown = await loadMapping(path, sourceOptions);
        return {
          content: [{
            type: 'text',
            text: jsonText({
              mapping_id,
              source_markdown: path,
              content_markdown: markdown,
              source: sourceContext(data.metadata, data.sourceRef, data.releaseTag)
            })
          }]
        };
      } catch (error) { return errorResult(error); }
    }
  );

  server.registerTool(
    'search_corpus_works',
    {
      description: 'Search the operational DIO/ODI publication registry by title, ID, type or DOI. Returns registered source records, not newly inferred publications.',
      inputSchema: {
        query: z.string().min(1).max(200),
        limit: z.number().int().min(1).max(30).default(10)
      }
    },
    async ({ query, limit }) => {
      try {
        const data = await loadData(sourceOptions);
        const works = Array.isArray(data.works.works) ? data.works.works as JsonObject[] : [];
        const needle = query.toLocaleLowerCase('en');
        const results = works
          .filter((work) => JSON.stringify(publicationSummary(work)).toLocaleLowerCase('en').includes(needle))
          .slice(0, limit)
          .map(publicationSummary);
        return {
          content: [{
            type: 'text',
            text: jsonText({
              query,
              total_returned: results.length,
              results,
              source: sourceContext(data.metadata, data.sourceRef, data.releaseTag)
            })
          }]
        };
      } catch (error) { return errorResult(error); }
    }
  );

  server.registerTool(
    'get_corpus_work',
    {
      description: 'Retrieve one publication record from the DIO/ODI works registry using its stable work ID.',
      inputSchema: { work_id: z.string().min(1).max(120) }
    },
    async ({ work_id }) => {
      try {
        const data = await loadData(sourceOptions);
        const works = Array.isArray(data.works.works) ? data.works.works as JsonObject[] : [];
        const work = works.find((item) => item.id === work_id);
        if (!work) return { content: [{ type: 'text', text: 'No corpus work found with ID ' + work_id + '.' }], isError: true };
        return {
          content: [{
            type: 'text',
            text: jsonText({
              record: work,
              source: sourceContext(data.metadata, data.sourceRef, data.releaseTag)
            })
          }]
        };
      } catch (error) { return errorResult(error); }
    }
  );

  server.registerResource(
    'reference-model-metadata',
    'dio-odi://reference-model/metadata',
    {
      title: 'DIO/ODI Reference Model metadata',
      description: 'Version, DOI, licence, namespace, and release metadata for the current archived Reference Model.',
      mimeType: 'application/json'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'application/json', text: jsonText(data.metadata) }] };
    }
  );

  server.registerResource(
    'reference-vocabulary-jsonld',
    'dio-odi://vocabulary/jsonld',
    {
      title: 'DIO/ODI Reference Vocabulary — JSON-LD',
      description: 'Canonical SKOS vocabulary in the archived v0.7.0 source snapshot.',
      mimeType: 'application/ld+json'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'application/ld+json', text: jsonText(data.vocabularyJsonLd) }] };
    }
  );

  server.registerResource(
    'reference-vocabulary-turtle',
    'dio-odi://vocabulary/turtle',
    {
      title: 'DIO/ODI Reference Vocabulary — Turtle',
      description: 'Canonical SKOS/RDF serialization of the Reference Vocabulary.',
      mimeType: 'text/turtle'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'text/turtle', text: data.vocabularyTurtle }] };
    }
  );

  server.registerResource(
    'reference-model-terminology',
    'dio-odi://reference-model/terminology',
    {
      title: 'DIO/ODI terminology',
      description: 'Human-readable terminology companion to the canonical vocabulary.',
      mimeType: 'text/markdown'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'text/markdown', text: data.terminology }] };
    }
  );

  server.registerResource(
    'reference-model-source-map',
    'dio-odi://reference-model/source-map',
    {
      title: 'DIO/ODI source map',
      description: 'Mapping of vocabulary concept clusters to their primary publications and current status.',
      mimeType: 'text/markdown'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'text/markdown', text: data.sourceMap }] };
    }
  );

  server.registerResource(
    'corpus-works',
    'dio-odi://corpus/works',
    {
      title: 'DIO/ODI corpus works registry',
      description: 'Versioned publication and software records for the DIO/ODI corpus.',
      mimeType: 'application/json'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'application/json', text: jsonText(data.works) }] };
    }
  );

  server.registerResource(
    'corpus-relations',
    'dio-odi://corpus/relations',
    {
      title: 'DIO/ODI corpus relations registry',
      description: 'Typed and status-qualified relations between works and representations.',
      mimeType: 'application/json'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'application/json', text: jsonText(data.relations) }] };
    }
  );

  server.registerResource(
    'corpus-references',
    'dio-odi://corpus/references',
    {
      title: 'DIO/ODI corpus canonical references',
      description: 'Canonical bibliographic records and persistent identifiers in the operational corpus registry.',
      mimeType: 'application/json'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'application/json', text: jsonText(data.references) }] };
    }
  );

  server.registerResource(
    'application-mappings-index',
    'dio-odi://mappings/index',
    {
      title: 'DIO/ODI application mappings index',
      description: 'Index of derived application mappings, separate from the canonical vocabulary.',
      mimeType: 'application/json'
    },
    async (uri) => {
      const data = await loadData(sourceOptions);
      return { contents: [{ uri: uri.href, mimeType: 'application/json', text: jsonText(mappingSummaries(data.metadata)) }] };
    }
  );

  server.registerResource(
    'reference-concept',
    new ResourceTemplate('dio-odi://concepts/{identifier}', { list: undefined }),
    {
      title: 'DIO/ODI concept record',
      description: 'A single concept resolved by local vocabulary ID, such as dio-odi://concepts/DIO.',
      mimeType: 'application/json'
    },
    async (uri, variables) => {
      const data = await loadData(sourceOptions);
      const identifier = String(variables.identifier ?? '');
      const matches = resolveConcept(data.vocabularyJsonLd, identifier);
      if (matches.length !== 1) throw new Error(matches.length === 0
        ? 'No exact concept match for ' + identifier + '.'
        : 'Ambiguous concept identifier ' + identifier + '.');
      const all = extractConcepts(data.vocabularyJsonLd);
      return {
        contents: [{
          uri: uri.href,
          mimeType: 'application/json',
          text: jsonText(conceptResponse(matches[0]!, all))
        }]
      };
    }
  );

  return server;
}
