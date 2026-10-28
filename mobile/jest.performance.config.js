module.exports = {
  ...require('./jest.config'),
  testMatch: ['**/*.benchmark.tsx'],
  moduleNameMapper: { '^@/(.*)$': '<rootDir>/src/$1' },
};
