/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,jsx,ts,tsx}', './src/**/*.{js,jsx,ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        canvas: '#F4F2EC',
        surface: '#FFFEFA',
        ink: '#102B28',
        muted: '#5D706B',
        brand: '#123F39',
        accent: '#F26749',
      },
      borderRadius: {
        card: '20px',
      },
    },
  },
  plugins: [],
};
