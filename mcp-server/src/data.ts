import type { JsonObject } from './catalog.js';
import { extractConcepts, vocabularyGraph } from './catalog.js';

const OWNER = 'dan-beranek';
const REPOSITORY = 'dio-odi-reference-model';
export const DEFAULT_SOURCE_REF = '264bb30b66be051998b4eb522ae1af8d376e15d7';
export const DEFAULT_EXPECTED_VERSION = '0.7.0';
const FETCH_TIMEOUT_MS = 15_000;
const MAX_TEXT_BYTES = 1_500_000;

const CORE_PATHS = [
  'metadata.json',
  'vocabulary/dio-odi.jsonld',
  'vocabulary/dio-odi-skos.ttl',
  'metadata/works.json',
  'metadata/references.json',
  'metadata/relations.json',
  'docs/terminology.md',
  'docs/source-map.md'
] as const;

const MAPPING_PATHS = new Set([
  'mappings/rag-pipeline-mapping.md',
  'mappings/hem-dio-mapping.md',
  'mappings/commit-boundary-policy-mapping.md',
  'mappings/agentic-er-commit-boundary-architecture-mapping.md'
]);

export type ReferenceModelMetadata = JsonObject & {
  version: string;
  reference_vocabulary_version: string;
  current_release: JsonObject;
  derived_application_mappings: JsonObject[];
};

export type DataBundle = {
  sourceRef: string;
  releaseTag: string;
  metadata: ReferenceModelMetadata;
  vocabularyJsonLd: JsonObject;
  vocabularyTurtle: string;
  works: JsonObject;
  references: JsonObject;
  relations: JsonObject;
  terminology: string;
  sourceMap: string;
};

export type DataSourceOptions = { sourceRef?: string; expectedVersion?: string };

const cachedData = new Map<string, Promise<DataBundle>>();
const mappingCache = new Map<string, Promise<string>>();

export function validateSourceRef(ref: string): string {
  if (!/^[A-Za-z0-9][A-Za-z0-9._/-]*$/.test(ref) || ref.includes('..') || ref.includes('//')) {
    throw new Error('DIO_ODI_SOURCE_REF must be a simple Git ref without traversal segments.');
  }
  return ref;
}

function rawUrl(ref: string, path: string): string {
  if (!CORE_PATHS.includes(path as typeof CORE_PATHS[number]) && !MAPPING_PATHS.has(path)) {
    throw new Error('Repository path is not on the MCP source allow-list: ' + path);
  }
  return 'https://raw.githubusercontent.com/' + OWNER + '/' + REPOSITORY + '/' + ref + '/' + path;
}

async function fetchText(ref: string, path: string): Promise<string> {
  const response = await fetch(rawUrl(ref, path), {
    headers: { accept: 'text/plain, application/json;q=0.9, */*;q=0.1' },
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS)
  });
  if (!response.ok) throw new Error('Unable to load ' + path + ' from ' + ref + ': HTTP ' + response.status + '.');
  const text = await response.text();
  if (new TextEncoder().encode(text).byteLength > MAX_TEXT_BYTES) {
    throw new Error('Repository file ' + path + ' exceeds the ' + MAX_TEXT_BYTES + '-byte safety limit.');
  }
  return text;
}

async function fetchJson<T extends JsonObject>(ref: string, path: string): Promise<T> {
  const text = await fetchText(ref, path);
  try {
    return JSON.parse(text) as T;
  } catch (error) {
    throw new Error('Invalid JSON in ' + path + ': ' + (error instanceof Error ? error.message : String(error)));
  }
}

function validateBundle(bundle: Omit<DataBundle, 'sourceRef'>, expectedVersion: string): void {
  if (bundle.metadata.version !== expectedVersion) {
    throw new Error('Source ref resolves to Reference Model ' + bundle.metadata.version + ', expected ' + expectedVersion + '.');
  }
  const release = bundle.metadata.current_release;
  if (release.version !== expectedVersion || release.archive_status !== 'archived' || typeof release.doi !== 'string') {
    throw new Error('Reference Model metadata does not identify the expected archived release.');
  }
  const graph = vocabularyGraph(bundle.vocabularyJsonLd);
  const scheme = graph.find((node) => node['@id'] === 'dio:ReferenceVocabulary');
  if (!scheme || scheme['owl:versionInfo'] !== bundle.metadata.reference_vocabulary_version) {
    throw new Error('The Reference Vocabulary JSON-LD version does not match metadata.json.');
  }
  if (extractConcepts(bundle.vocabularyJsonLd).length === 0) {
    throw new Error('The Reference Vocabulary contains no SKOS concepts.');
  }
  const works = Array.isArray(bundle.works.works) ? bundle.works.works as JsonObject[] : [];
  const model = works.find((work) => work.id === 'reference-model');
  const current = model && model.current_release && typeof model.current_release === 'object'
    ? model.current_release as JsonObject
    : undefined;
  if (!current || current.version !== expectedVersion || current.doi !== release.doi) {
    throw new Error('The operational works registry and metadata.json disagree about the archived Reference Model release.');
  }
  if (model?.reference_vocabulary_version !== bundle.metadata.reference_vocabulary_version) {
    throw new Error('The works registry and metadata.json disagree about the Reference Vocabulary version.');
  }
}

export async function loadData(options: DataSourceOptions = {}): Promise<DataBundle> {
  const sourceRef = validateSourceRef(options.sourceRef ?? DEFAULT_SOURCE_REF);
  const expectedVersion = options.expectedVersion ?? DEFAULT_EXPECTED_VERSION;
  const cacheKey = sourceRef + '::' + expectedVersion;
  let pending = cachedData.get(cacheKey);
  if (!pending) {
    pending = (async () => {
      const [metadata, vocabularyJsonLd, vocabularyTurtle, works, references, relations, terminology, sourceMap] =
        await Promise.all([
          fetchJson<ReferenceModelMetadata>(sourceRef, 'metadata.json'),
          fetchJson<JsonObject>(sourceRef, 'vocabulary/dio-odi.jsonld'),
          fetchText(sourceRef, 'vocabulary/dio-odi-skos.ttl'),
          fetchJson<JsonObject>(sourceRef, 'metadata/works.json'),
          fetchJson<JsonObject>(sourceRef, 'metadata/references.json'),
          fetchJson<JsonObject>(sourceRef, 'metadata/relations.json'),
          fetchText(sourceRef, 'docs/terminology.md'),
          fetchText(sourceRef, 'docs/source-map.md')
        ]);
      const bundleWithoutRef = {
        releaseTag: 'v' + expectedVersion,
        metadata,
        vocabularyJsonLd,
        vocabularyTurtle,
        works,
        references,
        relations,
        terminology,
        sourceMap
      };
      validateBundle(bundleWithoutRef, expectedVersion);
      return { sourceRef, ...bundleWithoutRef };
    })().catch((error) => {
      cachedData.delete(cacheKey);
      throw error;
    });
    cachedData.set(cacheKey, pending);
  }
  return pending;
}

export async function loadMapping(path: string, options: DataSourceOptions = {}): Promise<string> {
  if (!MAPPING_PATHS.has(path)) throw new Error('Application mapping path is not on the MCP allow-list.');
  const data = await loadData(options);
  const key = data.sourceRef + '::' + path;
  let pending = mappingCache.get(key);
  if (!pending) {
    pending = fetchText(data.sourceRef, path).catch((error) => {
      mappingCache.delete(key);
      throw error;
    });
    mappingCache.set(key, pending);
  }
  return pending;
}

export function resetDataCacheForTests(): void {
  cachedData.clear();
  mappingCache.clear();
}
