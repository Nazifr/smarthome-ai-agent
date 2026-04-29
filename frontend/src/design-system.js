// Design tokens — Mission Control aesthetic

export const colors = {
  // Base
  bg: '#0a0a0a',
  surface: '#141414',
  border: '#2a2a2a',

  // Text
  text: {
    primary: '#ffffff',
    secondary: '#a0a0a0',
    tertiary: '#666666',
  },

  // State colors
  accent: '#00d9ff',      // Cyan — active state
  success: '#00ff88',     // Green — good readings
  warning: '#ffaa00',     // Orange — alerts
  danger: '#ff3366',      // Red — critical

  // Actuator states
  on: '#00d9ff',
  off: '#333333',
  unknown: '#666666',
}

export const typography = {
  // Font stacks
  sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  mono: '"SF Mono", "Fira Code", "Consolas", monospace',

  // Sizes (rem)
  xs: '0.75rem',   // 12px
  sm: '0.875rem',  // 14px
  base: '1rem',    // 16px
  lg: '1.125rem',  // 18px
  xl: '1.25rem',   // 20px
  '2xl': '1.5rem', // 24px
  '3xl': '2rem',   // 32px
}

export const spacing = {
  xs: '0.5rem',   // 8px
  sm: '1rem',     // 16px
  md: '1.5rem',   // 24px
  lg: '2rem',     // 32px
  xl: '3rem',     // 48px
}

export const animations = {
  // Framer Motion variants
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },

  slideUp: {
    initial: { y: 20, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: -20, opacity: 0 },
  },

  slideRight: {
    initial: { x: '100%' },
    animate: { x: 0 },
    exit: { x: '100%' },
  },

  scale: {
    initial: { scale: 0.95, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 0.95, opacity: 0 },
  },

  // Transition presets
  spring: { type: 'spring', stiffness: 300, damping: 30 },
  smooth: { duration: 0.3, ease: [0.4, 0, 0.2, 1] },
  snap:   { duration: 0.15, ease: [0.4, 0, 1, 1] },
}
