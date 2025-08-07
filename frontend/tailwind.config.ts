import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Base colors using CSS variables
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        'glass-bg': 'var(--glass-bg)',
        'glass-border': 'var(--glass-border)',
        'glass-hover': 'var(--glass-hover)',
        
        // Existing glass system (enhanced for theme support)
        'glass': {
          50: 'var(--glass-50)',
          100: 'var(--glass-100)',
          200: 'var(--glass-200)',
          300: 'var(--glass-300)',
          400: 'var(--glass-400)',
          500: 'var(--glass-500)',
          600: 'var(--glass-600)',
          700: 'var(--glass-700)',
          800: 'var(--glass-800)',
          900: 'var(--glass-900)',
        },
        
        // Accent colors (theme-aware)
        'accent': {
          'blue': 'var(--accent-blue)',
          'purple': 'var(--accent-purple)',
          'cyan': 'var(--accent-cyan)',
          'pink': 'var(--accent-pink)',
          'orange': 'var(--accent-orange)',
          'green': 'var(--accent-green)',
          'indigo': 'var(--accent-indigo)',
          'yellow': 'var(--accent-yellow)',
        },
        
        // Enhanced semantic colors
        'primary': 'var(--primary)',
        'secondary': 'var(--secondary)',
        'muted': 'var(--muted)',
        'muted-foreground': 'var(--muted-foreground)',
        'card': 'var(--card)',
        'card-foreground': 'var(--card-foreground)',
        'popover': 'var(--popover)',
        'popover-foreground': 'var(--popover-foreground)',
        'border': 'var(--border)',
        'input': 'var(--input)',
        'ring': 'var(--ring)',
        
        // Dark color scale (enhanced)
        'dark': {
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
          950: '#0f1419',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-glass': 'var(--gradient-glass)',
        'gradient-primary': 'var(--gradient-primary)',
        'gradient-secondary': 'var(--gradient-secondary)',
        'gradient-accent': 'var(--gradient-accent)',
        'gradient-dark': 'var(--gradient-dark)',
        'gradient-light': 'var(--gradient-light)',
      },
      backdropBlur: {
        'xs': '2px',
        'glass': '20px',
        'glass-sm': '15px',
        'glass-md': '25px',
        'glass-lg': '30px',
        'glass-xl': '40px',
        'glass-2xl': '50px',
      },
      borderRadius: {
        'glass': '8px',
        'glass-sm': '6px',
        'glass-lg': '12px',
        'glass-xl': '14px',
        'glass-2xl': '18px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
        'glass-sm': '0 4px 16px 0 rgba(31, 38, 135, 0.25), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
        'glass-md': '0 12px 40px 0 rgba(31, 38, 135, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
        'glass-lg': '0 20px 60px 0 rgba(31, 38, 135, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.15)',
        'glass-xl': '0 25px 80px 0 rgba(31, 38, 135, 0.6), inset 0 1px 0 0 rgba(255, 255, 255, 0.2)',
        'glow': '0 0 20px rgba(100, 181, 246, 0.3)',
        'glow-sm': '0 0 10px rgba(100, 181, 246, 0.2)',
        'glow-md': '0 0 30px rgba(100, 181, 246, 0.4)',
        'glow-lg': '0 0 40px rgba(100, 181, 246, 0.5)',
        'glow-xl': '0 0 60px rgba(100, 181, 246, 0.6)',
        'inner-glow': 'inset 0 0 20px rgba(100, 181, 246, 0.1)',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'gradient-shift': 'gradient-shift 3s ease-in-out infinite',
        'bounce-slow': 'bounce 2s infinite',
        'spin-slow': 'spin 3s linear infinite',
        'ping-slow': 'ping 3s cubic-bezier(0, 0, 0.2, 1) infinite',
        'fade-in': 'fade-in 0.5s ease-out',
        'fade-in-up': 'fade-in-up 0.5s ease-out',
        'fade-in-down': 'fade-in-down 0.5s ease-out',
        'slide-in-left': 'slide-in-left 0.5s ease-out',
        'slide-in-right': 'slide-in-right 0.5s ease-out',
      },
      keyframes: {
        'float': {
          '0%, 100%': { 
            transform: 'translateY(0px) rotate(0deg)',
            opacity: '0.7'
          },
          '50%': { 
            transform: 'translateY(-20px) rotate(180deg)',
            opacity: '1'
          }
        },
        'pulse-glow': {
          '0%, 100%': { 
            boxShadow: '0 0 20px rgba(100, 181, 246, 0.3)'
          },
          '50%': { 
            boxShadow: '0 0 40px rgba(100, 181, 246, 0.6)'
          }
        },
        'gradient-shift': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' }
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        'fade-in-down': {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        'slide-in-left': {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' }
        },
        'slide-in-right': {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' }
        }
      },
      fontFamily: {
        'paperlogy': ['Paperlogy', 'Inter', 'system-ui', 'sans-serif'],
        'sans': ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Monaco', 'Consolas', 'monospace'],
      },
      fontSize: {
        'display': ['4rem', { lineHeight: '1.1', fontWeight: '900' }],
        'display-sm': ['3rem', { lineHeight: '1.2', fontWeight: '800' }],
        'hero': ['2.5rem', { lineHeight: '1.3', fontWeight: '700' }],
        'hero-sm': ['2rem', { lineHeight: '1.4', fontWeight: '600' }],
      },
      letterSpacing: {
        'tighter': '-0.05em',
        'tight': '-0.025em',
        'normal': '0em',
        'wide': '0.025em',
        'wider': '0.05em',
        'widest': '0.1em',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '92': '23rem',
        '96': '24rem',
        '104': '26rem',
        '112': '28rem',
        '128': '32rem',
      },
      screens: {
        'xs': '475px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
        '3xl': '1920px',
      },
    },
  },
  plugins: [],
}

export default config 