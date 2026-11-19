const { getDefaultConfig } = require('expo/metro-config');
const { withNativeWind } = require('nativewind/metro');

const config = getDefaultConfig(__dirname);
// Expo inlines this flag. A warm transform cache must follow the selected UI on rollback.
config.cacheVersion = JSON.stringify([config.cacheVersion, process.env.EXPO_PUBLIC_UI_VERSION ?? 'v2']);

module.exports = withNativeWind(config, { input: './global.css' });
