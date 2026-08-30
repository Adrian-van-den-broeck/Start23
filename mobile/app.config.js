const baseConfig = require('./app.json').expo;

const isWomboVariant = process.env.APP_VARIANT === 'wombo';

module.exports = {
  ...baseConfig,
  android: {
    ...baseConfig.android,
    package: isWomboVariant
      ? 'com.adrivdbs.wombo'
      : 'com.adrivdbs.start23',
  },
};
