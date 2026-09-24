import js from "@eslint/js";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    files: ["src/js/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.es2021,
        Chart: "readonly",
        tailwind: "readonly",
      },

    },
    rules: {
      // Catch undeclared variables and typos immediately
      "no-undef": "error",
      // Warn on unused variables (allow leading underscore for intentional ignores)
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      // Prevent unreachable code
      "no-unreachable": "warn",
      // Disallow duplicate keys in objects
      "no-dupe-keys": "error",
      // Disallow reassigning const variables
      "no-const-assign": "error",
      // Allow empty catch/finally blocks
      "no-empty": "off",
      // Allow function re-declarations in legacy scripts
      "no-redeclare": "off",
    },
  },
  {
    files: ["tests/frontend/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
        Chart: "readonly",
      },
    },
    rules: {
      "no-undef": "error",
      "no-unused-vars": "off",
    },
  },
];
