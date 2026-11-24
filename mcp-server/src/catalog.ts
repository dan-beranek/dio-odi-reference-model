export const VOCABULARY_NAMESPACE = 'https://vocab.danielberanek.cz/dio-odi/#';
const SKOS_CONCEPT = 'skos:Concept';

export type JsonObject = Record<string, unknown>;
export type Literal = { value: string; language?: string };
export type ConceptSummary = {
  id: string;
  uri: string;
  prefLabels: Literal[];
  altLabels: Literal[];
  definitions: Literal[];
  scopeNotes: Literal[];
  examples: Literal[];
  broader: string[];
  narrower: string[];
  related: string[];
  hasPart: string[];
  isPartOf: string[];
  sources: string[];
};

function asArray(value: unknown): unknown[] {
  return value === undefined || value === null ? [] : Array.isArray(value) ? value : [value];
}

function expandId(value: unknown): string {
  if (typeof value !== 'string') return '';
  return value.startsWith('dio:') ? VOCABULARY_NAMESPACE + value.slice(4) : value;
}

function localId(uri: string): string {
  return uri.startsWith(VOCABULARY_NAMESPACE) ? uri.slice(VOCABULARY_NAMESPACE.length) : uri;
}

function literalValues(value: unknown): Literal[] {
  return asArray(value).flatMap((item): Literal[] => {
    if (typeof item === 'string') return [{ value: item }];
    if (!item || typeof item !== 'object' || Array.isArray(item)) return [];
    const object = item as JsonObject;
    if (typeof object['@value'] !== 'string') return [];
    const literal: Literal = { value: object['@value'] as string };
    if (typeof object['@language'] === 'string') literal.language = object['@language'] as string;
    return [literal];
  });
}

function idValues(value: unknown): string[] {
  return asArray(value).flatMap((item) => {
    if (typeof item === 'string') return [expandId(item)];
    if (!item || typeof item !== 'object' || Array.isArray(item)) return [];
    const id = (item as JsonObject)['@id'];
    return typeof id === 'string' ? [expandId(id)] : [];
  }).filter(Boolean);
}

function hasType(node: JsonObject, type: string): boolean {
  return asArray(node['@type']).some((item) => item === type);
}

export function vocabularyGraph(jsonld: JsonObject): JsonObject[] {
  const graph = jsonld['@graph'];
  if (!Array.isArray(graph)) throw new Error('Vocabulary JSON-LD has no @graph array.');
  return graph.filter((item): item is JsonObject =>
    Boolean(item) && typeof item === 'object' && !Array.isArray(item));
}

export function extractConcepts(jsonld: JsonObject): ConceptSummary[] {
  return vocabularyGraph(jsonld)
    .filter((node) => hasType(node, SKOS_CONCEPT))
    .map((node) => {
      const uri = expandId(node['@id']);
      if (!uri) throw new Error('A SKOS concept is missing @id.');
      return {
        id: localId(uri),
        uri,
        prefLabels: literalValues(node['skos:prefLabel']),
        altLabels: literalValues(node['skos:altLabel']),
        definitions: literalValues(node['skos:definition']),
        scopeNotes: literalValues(node['skos:scopeNote']),
        examples: literalValues(node['skos:example']),
        broader: idValues(node['skos:broader']),
        narrower: idValues(node['skos:narrower']),
        related: idValues(node['skos:related']),
        hasPart: idValues(node['dcterms:hasPart']),
        isPartOf: idValues(node['dcterms:isPartOf']),
        sources: idValues(node['dcterms:source'])
      };
    })
    .sort((a, b) => a.id.localeCompare(b.id));
}

function searchableText(concept: ConceptSummary): string {
  return [
    concept.id, concept.uri,
    ...concept.prefLabels.map((item) => item.value),
    ...concept.altLabels.map((item) => item.value),
    ...concept.definitions.map((item) => item.value),
    ...concept.scopeNotes.map((item) => item.value)
  ].join('\n').toLocaleLowerCase('en');
}

export function searchConcepts(jsonld: JsonObject, query: string, limit = 10): ConceptSummary[] {
  const needle = query.trim().toLocaleLowerCase('en');
  if (!needle) return [];
  const results = extractConcepts(jsonld).flatMap((concept) => {
    const ids = [concept.id, concept.uri].map((item) => item.toLocaleLowerCase('en'));
    const pref = concept.prefLabels.map((item) => item.value.toLocaleLowerCase('en'));
    const alt = concept.altLabels.map((item) => item.value.toLocaleLowerCase('en'));
    const all = searchableText(concept);
    let score = 0;
    if (ids.includes(needle) || pref.includes(needle)) score = 100;
    else if (alt.includes(needle)) score = 90;
    else if (pref.some((item) => item.includes(needle))) score = 80;
    else if (alt.some((item) => item.includes(needle))) score = 70;
    else if (all.includes(needle)) score = 50;
    return score ? [{ concept, score }] : [];
  });
  return results
    .sort((a, b) => b.score - a.score || a.concept.id.localeCompare(b.concept.id))
    .slice(0, limit)
    .map((item) => item.concept);
}

export function resolveConcept(jsonld: JsonObject, identifier: string): ConceptSummary[] {
  const needle = identifier.trim().toLocaleLowerCase('en');
  if (!needle) return [];
  return extractConcepts(jsonld).filter((concept) => [
    concept.id, concept.uri, 'dio:' + concept.id,
    ...concept.prefLabels.map((item) => item.value),
    ...concept.altLabels.map((item) => item.value)
  ].some((candidate) => candidate.toLocaleLowerCase('en') === needle));
}

export function expandConceptId(identifier: string): string {
  const value = identifier.trim();
  if (value.startsWith('dio:')) return expandId(value);
  if (/^[A-Za-z][A-Za-z0-9._-]*$/.test(value)) return VOCABULARY_NAMESPACE + value;
  return value;
}
