/** Generate the only frontend API types from the workspace contract. */
export default {
  input: '../contracts/openapi.yaml',
  output: './src/generated/api.ts',
  client: 'fetch',
};

