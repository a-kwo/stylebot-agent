import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cream: '#faf9f7',
        ink: '#1a1a1a',
        muted: '#6b7280',
        accent: '#1a1a1a',
        'accent-light': '#374151',
        border: '#e5e5e5',
        'border-dark': '#374151',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
