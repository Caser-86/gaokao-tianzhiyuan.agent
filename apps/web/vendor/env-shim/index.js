const { createNapiModule } = require('@emnapi/core');
const { createContext } = require('@emnapi/runtime');

const napiModule = createNapiModule({
  context: createContext(),
  filename: 'next-swc-wasm-nodejs',
});

module.exports = {
  ...napiModule.imports.env,
  ...napiModule.imports.napi,
};
