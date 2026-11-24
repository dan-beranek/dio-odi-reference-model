import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_SOURCE_REF, loadData, loadMapping, resetDataCacheForTests, validateSourceRef } from '../src/data.js';
import { extractConcepts } from '../src/catalog.js';

test('accepts the pinned immutable metadata commit', () => {
  const ref = '264bb30b66be051998b4eb522ae1af8d376e15d7';
  assert.equal(validateSourceRef(ref), ref);
});

test('rejects traversal and unsafe ref syntax', () => {
  assert.throws(() => validateSourceRef('../main'));
  assert.throws(() => validateSourceRef('refs/heads/../../main'));
  assert.throws(() => validateSourceRef('main?foo=bar'));
});


test('loads and validates the pinned archived v0.7.0 source bundle', {
  skip: process.env.DIO_ODI_LIVE_SOURCE_CHECK !== '1'
}, async () => {
  resetDataCacheForTests();
  const data = await loadData();

  assert.equal(data.sourceRef, DEFAULT_SOURCE_REF);
  assert.equal(data.metadata.version, '0.7.0');
  assert.equal(data.metadata.current_release.doi, '10.5281/zenodo.24020300');
  assert.equal(data.metadata.reference_vocabulary_version, '0.2.1');
  assert.equal(extractConcepts(data.vocabularyJsonLd).length, 40);

  const works = data.works.works as Array<Record<string, unknown>>;
  const model = works.find((work) => work.id === 'reference-model');
  assert.equal((model?.current_release as Record<string, unknown>)?.doi, '10.5281/zenodo.24020300');

  const mapping = await loadMapping('mappings/agentic-er-commit-boundary-architecture-mapping.md');
  assert.ok(mapping.includes('120'));
  assert.ok(mapping.includes('206'));
});
