const path = require('path');
const mobile = path.resolve(__dirname, '../../../mobile');
module.exports = {
  ...require(path.join(mobile, 'jest.config.js')),
  rootDir: mobile,
  roots: [mobile, __dirname],
  modulePaths: [path.join(mobile, 'node_modules')],
  testMatch: ['**/audit-*.test.tsx'],
  moduleNameMapper: { '^@/(.*)$': '<rootDir>/src/$1' },
  cacheDirectory: path.resolve(__dirname, '../../../.audit-probe-cache'),
};
