import packageJson from '../package.json';

test('declares a reproducible vitest toolchain for the web workspace', () => {
  expect(packageJson.scripts.dev).toBe('node ./node_modules/next/dist/bin/next dev');
  expect(packageJson.scripts.build).toBe('node ./node_modules/next/dist/bin/next build');
  expect(packageJson.scripts.test).toBe('node ./node_modules/vitest/vitest.mjs run');
  expect(packageJson.devDependencies.rollup).toBe('npm:@rollup/wasm-node@4.60.1');
});
