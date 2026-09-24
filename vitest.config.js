import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "happy-dom",
    globals: true,
    isolate: false,
    fileParallelism: false,
    include: ["tests/frontend/**/*.test.js"]
  }
});

