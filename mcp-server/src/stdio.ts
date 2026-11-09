import { serveStdio } from '@modelcontextprotocol/server/stdio';
import { createDioOdiServer } from './server.js';
import { DEFAULT_EXPECTED_VERSION, DEFAULT_SOURCE_REF } from './data.js';

const sourceOptions = {
  sourceRef: process.env.DIO_ODI_SOURCE_REF ?? DEFAULT_SOURCE_REF,
  expectedVersion: process.env.DIO_ODI_EXPECTED_VERSION ?? DEFAULT_EXPECTED_VERSION
};

void serveStdio(() => createDioOdiServer(sourceOptions));
console.error('DIO/ODI Reference Model MCP server ready (stdio; read-only).');
