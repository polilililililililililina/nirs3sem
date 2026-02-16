module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'next/core-web-vitals',
    'plugin:import/recommended',
    'plugin:import/typescript', 
    'plugin:@typescript-eslint/recommended',
    'prettier'
  ],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    },
    project: './tsconfig.json'
  },
  plugins: [
    '@typescript-eslint',
    'import',
    'unused-imports'
  ],
  rules: {
    // Import rules
    'import/no-unresolved': 'error',
    'import/no-cycle': 'error',
    'import/no-default-export': 'off',
    'import/prefer-default-export': 'off',
    'import/no-extraneous-dependencies': [
      'error',
      {
        'devDependencies': [
          '**/*.test.{ts,tsx}',
          '**/*.spec.{ts,tsx}',
          '**/*.stories.{ts,tsx}',
          '**/test/**',
          '**/__tests__/**'
        ]
      }
    ],
    'import/order': [
      'error',
      {
        'groups': [
          'builtin',
          'external',
          'internal',
          'parent',
          'sibling',
          'index'
        ],
        'newlines-between': 'always',
        'alphabetize': {
          'order': 'asc',
          'caseInsensitive': true
        },
        'pathGroups': [
          {
            'pattern': 'react',
            'group': 'external',
            'position': 'before'
          },
          {
            'pattern': 'next/**',
            'group': 'external',
            'position': 'before'
          },
          {
            'pattern': '@features/**',
            'group': 'internal',
            'position': 'before'
          },
          {
            'pattern': '@entities/**',
            'group': 'internal'
          },
          {
            'pattern': '@shared/**',
            'group': 'internal'
          },
          {
            'pattern': '@widgets/**',
            'group': 'internal'
          },
          {
            'pattern': '@providers/**',
            'group': 'internal'
          }
        ],
        'pathGroupsExcludedImportTypes': ['react']
      }
    ],

    // TypeScript rules
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        'argsIgnorePattern': '^_',
        'varsIgnorePattern': '^_'
      }
    ],
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/ban-ts-comment': 'warn',
    '@typescript-eslint/no-non-null-assertion': 'off',

    // React rules
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    'react/display-name': 'off',

    // JavaScript rules
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'warn',
    'no-unused-vars': 'off', // Используем @typescript-eslint/no-unused-vars вместо
    'camelcase': 'off',
    'semi': 'off', // Используем TypeScript правило
    '@typescript-eslint/semi': ['error', 'never'],

    // Unused imports
    'unused-imports/no-unused-imports': 'error',
    'unused-imports/no-unused-vars': 'off', // Используем @typescript-eslint/no-unused-vars

    // Next.js specific
    '@next/next/no-img-element': 'warn',
    '@next/next/no-sync-scripts': 'error'
  },
  overrides: [
    {
      files: ['*.ts', '*.tsx'],
      rules: {
        // Можно добавить специфичные правила для TypeScript файлов
      }
    },
    {
      files: ['pages/**/*.tsx', 'pages/**/*.ts'],
      rules: {
        'import/no-default-export': 'off',
        'import/prefer-default-export': 'error'
      }
    },
    {
      files: ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts', '**/*.spec.tsx'],
      rules: {
        'import/no-extraneous-dependencies': 'off'
      }
    }
  ],
  settings: {
    'import/parsers': {
      '@typescript-eslint/parser': ['.ts', '.tsx']
    },
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true,
        project: './tsconfig.json'
      },
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
        moduleDirectory: ['node_modules', 'src/']
      }
    },
    'react': {
      version: 'detect'
    }
  },
  ignorePatterns: [
    'node_modules/',
    '.next/',
    'dist/',
    'build/',
    '*.config.js',
    '*.config.ts',
    '**/*.d.ts'
  ]
}