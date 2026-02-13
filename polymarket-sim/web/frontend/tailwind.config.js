/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#09090B',
          secondary: '#18181B',
        },
        text: {
          high: '#E4E4E7',
          medium: '#71717A',
          low: '#3F3F46',
        },
        accent: '#3B82F6',
        success: '#10B981',
        error: '#EF4444',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      spacing: {
        '0': '0',
        '8': '8px',
        '16': '16px',
        '40': '40px',
      },
      borderRadius: {
        '8': '8px',
      },
    },
  },
  plugins: [],
}
