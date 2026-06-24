// ESLint flat config for gaokao-agent-web
// 使用 Next.js 推荐规则 + TypeScript 检查
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import nextPlugin from '@next/eslint-plugin-next';

export default tseslint.config(
  // 全局忽略
  {
    ignores: [
      '.next/**',
      'node_modules/**',
      'vendor/**',
      'coverage/**',
      '**/*.config.{js,mjs,ts}',
      'next-env.d.ts',
    ],
  },

  // 基础 JS 推荐规则
  js.configs.recommended,

  // TypeScript 推荐规则（类型感知可选，此处用轻量版避免 CI 装类型依赖过重）
  ...tseslint.configs.recommended,

  // Next.js 规则
  {
    files: ['**/*.{ts,tsx,js,jsx}'],
    plugins: {
      '@next/next': nextPlugin,
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs['core-web-vitals'].rules,
    },
  },

  // 项目自定义规则
  {
    files: ['**/*.{ts,tsx}'],
    rules: {
      // 与 TypeScript 严格模式协同：no-unused-vars 由 tsc 处理，eslint 仅警告
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      // 允许 void 返回值作为丢弃
      '@typescript-eslint/no-confusing-void-expression': 'off',
      // React 19 + Next 15 不需要 import React
      'react/react-in-jsx-scope': 'off',
    },
  },

  // 测试文件放宽
  {
    files: ['tests/**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
    },
  },
);
