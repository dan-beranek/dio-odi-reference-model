import test from 'node:test';
import assert from 'node:assert/strict';
import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client';
import { createMcpHandler } from '@modelcontextprotocol/server';
import { createDioOdiServer } from '../src/server.js';
import { resetDataCacheForTests } from '../src/data.js';

const DOI = '10.5281/zenodo.24020300';
const fixtures: Record<string, string> = {
  'metadata.json': JSON.stringify({
    title: 'DIO/ODI Reference Model',
    version: '0.7.0',
    status: 'archived',
    namespace: 'https://vocab.danielberanek.cz/dio-odi/#',
    repository: 'https://github.com/dan-beranek/dio-odi-reference-model',
    license: 'CC-BY-4.0',
    reference_vocabulary_version: '0.2.1',
    current_release: { version: '0.7.0', archive_status: 'archived', doi: DOI, doi_url: 'https://doi.org/' + DOI },
    derived_application_mappings: [{
      title: 'Application Mapping: DIO Reconstruction Failure Modes × RAG Pipeline',
      path: 'mappings/rag-pipeline-mapping.md',
      relation: 'derived-application-layer',
      release_status: 'included-in-0.7.0',
      archived_release_doi: DOI,
      frontend: 'https://vocab.danielberanek.cz/mappings/rag-pipeline/'
    }]
  }),
  'vocabulary/dio-odi.jsonld': JSON.stringify({
    '@context': { dio: 'https://vocab.danielberanek.cz/dio-odi/#' },
    '@graph': [
      { '@id': 'dio:ReferenceVocabulary', '@type': 'skos:ConceptScheme', 'owl:versionInfo': '0.2.1' },
      {
        '@id': 'dio:DIO',
        '@type': 'skos:Concept',
        'skos:prefLabel': { '@value': 'Digital Identity Optimization', '@language': 'en' },
        'skos:altLabel': { '@value': 'DIO', '@language': 'en' },
        'skos:definition': { '@value': 'An applied discipline concerned with digital identity reconstruction.', '@language': 'en' },
        'dcterms:source': [{ '@id': 'https://doi.org/10.5281/zenodo.21610934' }]
      }
    ]
  }),
  'vocabulary/dio-odi-skos.ttl': '@prefix dio: <https://vocab.danielberanek.cz/dio-odi/#> .\ndio:DIO a <http://www.w3.org/2004/02/skos/core#Concept> .\n',
  'metadata/works.json': JSON.stringify({
    works: [{
      id: 'reference-model',
      title: 'DIO/ODI Reference Model',
      reference_vocabulary_version: '0.2.1',
      current_release: { version: '0.7.0', doi: DOI }
    }]
  }),
  'metadata/references.json': JSON.stringify({ references: [] }),
  'metadata/relations.json': JSON.stringify({ relations: [] }),
  'docs/terminology.md': '# DIO/ODI terminology fixture',
  'docs/source-map.md': '# DIO/ODI source map fixture',
  'mappings/rag-pipeline-mapping.md': '# RAG mapping fixture\n\nA derived mapping.'
};

test('serves read-only tools and resources over Streamable HTTP', async () => {
  const previousFetch = globalThis.fetch;
  resetDataCacheForTests();
  globalThis.fetch = async (input: RequestInfo | URL) => {
    const url = new URL(String(input));
    const marker = '/test-fixture/';
    const index = url.pathname.indexOf(marker);
    const path = index >= 0 ? url.pathname.slice(index + marker.length) : '';
    const body = fixtures[path];
    return body === undefined
      ? new Response('Not found', { status: 404 })
      : new Response(body, { status: 200, headers: { 'content-type': 'application/json; charset=utf-8' } });
  };

  const handler = createMcpHandler(() => createDioOdiServer({
    sourceRef: 'test-fixture',
    expectedVersion: '0.7.0'
  }));
  const client = new Client(
    { name: 'dio-odi-mcp-test', version: '1.0.0' },
    { versionNegotiation: { mode: 'auto' } }
  );
  const transport = new StreamableHTTPClientTransport(new URL('http://test.local/mcp'), {
    fetch: (url, init) => handler.fetch(new Request(url, init))
  });

  try {
    await client.connect(transport);
    const listed = await client.listTools();
    const names = listed.tools.map((tool) => tool.name);
    assert.ok(names.includes('get_reference_model_info'));
    assert.ok(names.includes('search_concepts'));
    assert.ok(names.includes('get_application_mapping'));

    const info = await client.callTool({ name: 'get_reference_model_info', arguments: {} });
    const infoText = info.content.find((part) => part.type === 'text')?.text ?? '';
    assert.ok(infoText.includes(DOI));

    const found = await client.callTool({ name: 'search_concepts', arguments: { query: 'DIO' } });
    const foundText = found.content.find((part) => part.type === 'text')?.text ?? '';
    assert.ok(foundText.includes('Digital Identity Optimization'));

    const mapping = await client.callTool({
      name: 'get_application_mapping',
      arguments: { mapping_id: 'rag-pipeline' }
    });
    const mappingText = mapping.content.find((part) => part.type === 'text')?.text ?? '';
    assert.ok(mappingText.includes('A derived mapping.'));

    const resource = await client.readResource({ uri: 'dio-odi://reference-model/metadata' });
    assert.ok(resource.contents[0]?.text?.includes(DOI));
    const references = await client.readResource({ uri: 'dio-odi://corpus/references' });
    assert.ok(references.contents[0]?.text?.includes('references'));
  } finally {
    await client.close();
    await handler.close();
    globalThis.fetch = previousFetch;
    resetDataCacheForTests();
  }
});
