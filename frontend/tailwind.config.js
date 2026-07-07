/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        sovereign: {
          dark: '#060b18',
          navy: '#0a0f1e',
          blue: '#0d1529',
          panel: '#111827',
          border: '#1e2d4a',
          cyan: '#00d4ff',
          green: '#00ff88',
          red: '#ff3b6b',
          yellow: '#ffd700',
          orange: '#ff6b35',
        }
      },
      fontFamily: {
        arabic: ['Cairo', 'Arial', 'sans-serif'],
      }
    }
  },
  plugins: []
}
