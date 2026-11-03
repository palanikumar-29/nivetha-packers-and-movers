/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './core/templates/**/*.html',
    './templates/**/*.html',
    './core/views.py',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        theme: {
          page: 'var(--color-bg-page)',
          alt: 'var(--color-bg-alt)',
          surface: 'var(--color-bg-surface)',
          heading: 'var(--color-text-heading)',
          body: 'var(--color-text-body)',
          muted: 'var(--color-text-muted)',
          border: 'var(--color-border)',
          header: 'var(--color-bg-header)',
          footer: 'var(--color-bg-footer)',
          'footer-text': 'var(--color-text-footer)',
          'footer-muted': 'var(--color-text-footer-muted)',
        },
        lorry: {
          orange: '#F26B1D',
          'orange-hover': '#E05E13',
          dark: '#1F2933',
        },
        route: {
          green: '#0B6B3A',
        },
      },
      fontFamily: {
        sans: ['"Hind Madurai"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
