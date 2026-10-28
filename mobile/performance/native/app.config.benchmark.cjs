// Copy to mobile/app.config.js only in a disposable benchmark worktree.
module.exports = ({ config }) => ({
  ...config,
  name: 'Wombo A9 Benchmark',
  scheme: 'wombo-a9-benchmark',
  android: { ...config.android, package: 'com.adrivdbs.wombo.a9benchmark' },
});
