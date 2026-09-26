// @ts-check
// Flat ESLint config shared by apps/web and packages/ui.
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['node_modules/**', '**/.next/**', '**/dist/**', '**/.nx/**'] },
  ...tseslint.configs.recommended.map((config) => ({
    files: ['**/*.{ts,tsx}'],
    ...config,
  })),
  {
    files: ['**/*.{ts,tsx}'],
    plugins: { '@typescript-eslint': tseslint.plugin },
    rules: {
      // This codebase passes dynamic tool arguments as `any`-ish payloads.
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  },
);
