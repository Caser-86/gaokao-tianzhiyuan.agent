import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';

import nextConfig from '../next.config.mjs';

const require = createRequire(import.meta.url);

test('opts into the wasm compiler path for constrained builds', () => {
  expect(nextConfig.experimental?.useWasmBinary).toBe(true);
  expect(existsSync(new URL('../next.config.ts', import.meta.url))).toBe(false);
});

test('loads the installed Next compiler runtime entrypoint', () => {
  const swcRuntimePath = require.resolve('next/dist/build/swc/index.js');

  expect(existsSync(swcRuntimePath)).toBe(true);
});
