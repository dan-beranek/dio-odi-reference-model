import test from 'node:test';
import assert from 'node:assert/strict';
import { extractConcepts, resolveConcept, searchConcepts, VOCABULARY_NAMESPACE } from '../src/catalog.js';

const fixture = {
  '@graph': [
    { '@id': 'dio:ReferenceVocabulary', '@type': 'skos:ConceptScheme', 'owl:versionInfo': '0.2.1' },
    {
      '@id': 'dio:DIO',
      '@type': 'skos:Concept',
      'skos:inScheme': { '@id': 'dio:ReferenceVocabulary' },
      'skos:prefLabel': { '@value': 'Digital Identity Optimization', '@language': 'en' },
      'skos:altLabel': { '@value': 'DIO', '@language': 'en' },
      'skos:definition': { '@value': 'An applied discipline.', '@language': 'en' },
      'skos:related': [{ '@id': 'dio:ODI' }],
      'dcterms:source': [{ '@id': 'https://doi.org/10.5281/zenodo.21610934' }]
    },
    {
      '@id': 'dio:ODI',
      '@type': ['skos:Concept'],
      'skos:prefLabel': { '@value': 'Ontology of Digital Identity', '@language': 'en' },
      'skos:altLabel': { '@value': 'ODI', '@language': 'en' }
    }
  ]
};

test('extracts SKOS concepts and expands canonical identifiers', () => {
  const concepts = extractConcepts(fixture);
  assert.equal(concepts.length, 2);
  assert.equal(concepts[0]?.uri, VOCABULARY_NAMESPACE + 'DIO');
  assert.equal(concepts[0]?.definitions[0]?.value, 'An applied discipline.');
  assert.deepEqual(concepts[0]?.related, [VOCABULARY_NAMESPACE + 'ODI']);
});

test('resolves exact local IDs, compact IDs, labels and alternative labels', () => {
  assert.equal(resolveConcept(fixture, 'DIO')[0]?.id, 'DIO');
  assert.equal(resolveConcept(fixture, 'dio:DIO')[0]?.id, 'DIO');
  assert.equal(resolveConcept(fixture, 'Digital Identity Optimization')[0]?.id, 'DIO');
  assert.equal(resolveConcept(fixture, 'ODI')[0]?.id, 'ODI');
});

test('searches labels and definitions without inventing results', () => {
  assert.equal(searchConcepts(fixture, 'applied discipline')[0]?.id, 'DIO');
  assert.equal(searchConcepts(fixture, 'not a concept').length, 0);
  assert.equal(searchConcepts(fixture, 'identity', 1).length, 1);
});

test('reports ambiguous aliases rather than choosing an arbitrary concept', () => {
  const ambiguous = {
    '@graph': [
      { '@id': 'dio:Alpha', '@type': 'skos:Concept', 'skos:prefLabel': { '@value': 'Alpha', '@language': 'en' }, 'skos:altLabel': { '@value': 'Shared', '@language': 'en' } },
      { '@id': 'dio:Beta', '@type': 'skos:Concept', 'skos:prefLabel': { '@value': 'Beta', '@language': 'en' }, 'skos:altLabel': { '@value': 'Shared', '@language': 'en' } }
    ]
  };
  assert.equal(resolveConcept(ambiguous, 'Shared').length, 2);
});
