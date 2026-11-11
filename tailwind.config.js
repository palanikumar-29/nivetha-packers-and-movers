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
          link: 'var(--color-link)',
          'link-hover': 'var(--color-link-hover)',
          'focus-ring': 'var(--color-focus-ring)',
        },
        btn: {
          'primary-bg': 'var(--btn-primary-bg)',
          'primary-text': 'var(--btn-primary-text)',
          'primary-hover': 'var(--btn-primary-hover)',
          'secondary-outline': 'var(--btn-secondary-outline)',
          'secondary-text': 'var(--btn-secondary-text)',
          'secondary-hover-bg': 'var(--btn-secondary-hover-bg)',
          'secondary-hover-text': 'var(--btn-secondary-hover-text)',
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
