/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        space: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        cosmic: {
          pearl: '#fafbff',
          starlight: '#f0f3ff',
          nebula: '#f5f3ff',
          aurora: '#ecfeff',
          solar: '#fffbeb',
        },
        celestial: {
          indigo: '#4f46e5',
          purple: '#7c3aed',
          violet: '#8b5cf6',
          fuchsia: '#c026d3',
          cyan: '#06b6d4',
          amber: '#f59e0b',
          emerald: '#10b981',
          rose: '#f43f5e',
        }
      },
      backgroundImage: {
        'nebula-gradient': 'radial-gradient(ellipse at top left, rgba(224, 231, 255, 0.6) 0%, rgba(243, 232, 255, 0.4) 40%, rgba(254, 243, 199, 0.3) 70%, rgba(248, 250, 252, 0.8) 100%)',
        'aurora-card': 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(245, 243, 255, 0.8) 100%)',
        'solar-gradient': 'linear-gradient(135deg, #f59e0b 0%, #ec4899 50%, #6366f1 100%)',
        'orbit-gradient': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%)',
        'emerald-orbit': 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
      },
      boxShadow: {
        'celestial-sm': '0 2px 8px -2px rgba(99, 102, 241, 0.08), 0 1px 4px -1px rgba(0, 0, 0, 0.04)',
        'celestial': '0 10px 25px -3px rgba(99, 102, 241, 0.08), 0 4px 10px -2px rgba(0, 0, 0, 0.03)',
        'celestial-lg': '0 20px 40px -6px rgba(99, 102, 241, 0.12), 0 8px 16px -4px rgba(0, 0, 0, 0.04)',
        'glow-indigo': '0 0 25px -3px rgba(99, 102, 241, 0.35)',
        'glow-amber': '0 0 25px -3px rgba(245, 158, 11, 0.4)',
        'glow-emerald': '0 0 25px -3px rgba(16, 185, 129, 0.35)',
      },
      borderRadius: {
        '2.5xl': '20px',
        '3xl': '24px',
        '4xl': '32px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
