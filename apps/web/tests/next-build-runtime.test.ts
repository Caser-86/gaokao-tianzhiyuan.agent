import { existsSync } from 'node:fs';

import nextConfig from '../next.config.mjs';

test('opts into the wasm compiler path for constrained builds', () => {
  expect(nextConfig.experimental?.useWasmBinary).toBe(true);
  expect(existsSync(new URL('../next.config.ts', import.meta.url))).toBe(false);
});

test('loads the Next wasm bindings through the repository-owned env bridge', async () => {
  const bindings = await import('next/wasm/@next/swc-wasm-nodejs/wasm.js');

  expect(bindings.transformSync).toEqual(expect.any(Function));
});
