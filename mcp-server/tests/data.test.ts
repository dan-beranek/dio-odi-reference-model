import test from 'node:test';
import assert from 'node:assert/strict';
import { validateSourceRef } from '../src/data.js';

test('accepts the pinned immutable metadata commit', () => {
  const ref = '264bb30b66be051998b4eb522ae1af8d376e15d7';
  assert.equal(validateSourceRef(ref), ref);
});

test('rejects traversal and unsafe ref syntax', () => {
  assert.throws(() => validateSourceRef('../main'));
  assert.throws(() => validateSourceRef('refs/heads/../../main'));
  assert.throws(() => validateSourceRef('main?foo=bar'));
});
