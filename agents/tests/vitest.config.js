import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['**/*.test.js'],
    // Agents import from @langchain/* which requires LangChain to be installed.
    // The tests mock the BaseAgent class entirely, so we don't need the real deps.
    // If tests are run from within an agent directory that has node_modules, they
    // can also resolve the real imports.
    testTimeout: 10000,
  },
});
