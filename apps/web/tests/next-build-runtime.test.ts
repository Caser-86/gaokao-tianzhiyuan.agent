import nextConfig from '../next.config';

test('opts into the wasm compiler path for constrained builds', () => {
  expect(nextConfig.experimental?.useWasmBinary).toBe(true);
});

test('loads the Next wasm bindings through the repository-owned env bridge', async () => {
  const bindings = await import('next/wasm/@next/swc-wasm-nodejs/wasm.js');

  expect(bindings.transformSync).toEqual(expect.any(Function));
});
