/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        app: 'var(--color-bg)',
        surface: {
          DEFAULT: 'var(--color-surface)',
          hover: 'var(--color-surface-hover)',
        },
        primary: {
          DEFAULT: 'var(--color-text-primary)',
          interactive: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
        },
        accent: {
          sage: 'var(--color-accent)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
        },
        border: {
          hairline: 'var(--color-border-hairline)',
          subtle: 'var(--color-border-subtle)',
        },
      },
      fontFamily: {
        sans: ['Supreme', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      maxWidth: {
        content: 'var(--content-max-width)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      },
      boxShadow: {
        'neumorphic-card': 'var(--shadow-neumorphic-card)',
        'neumorphic-elevated': 'var(--shadow-neumorphic-elevated)',
        'neumorphic-inset': 'var(--shadow-neumorphic-inset)',
      },
      transitionTimingFunction: {
        tactile: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
};
