module.exports = {
  content: ['./*.php', './template-parts/**/*.php'],
  theme: {
    extend: {
      colors: {
        canvas: '#010102',
        accent: '#5e6ad2',
        'accent-hover': '#828fff',
        'surface-1': '#0f1011',
        'surface-2': '#141516',
        'surface-3': '#18191a',
        'border-hairline': '#23252a',
        'border-strong': '#34343a',
        ink: '#f7f8f8',
        'text-muted': '#d0d6e0',
        'text-subtle': '#8a8f98',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'serif'],
      },
    },
  },
  plugins: [],
};
