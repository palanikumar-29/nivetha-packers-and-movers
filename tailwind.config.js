/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './core/templates/**/*.html',
    './core/views.py',
    './templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        asphalt: '#1e2124',
        highway: '#15803d',
        signal: '#f59e0b',
      },
    },
  },
  plugins: [],
}

