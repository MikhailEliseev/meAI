import * as esbuild from 'esbuild';

await esbuild.build({
  entryPoints: ['src/index.jsx'],
  bundle: true,
  outfile: 'dist/chat-bundle.js',
  format: 'iife',
  minify: true,
  external: ['react', 'react-dom'],
  jsx: 'automatic',
  loader: { '.css': 'text' },
});

// Also bundle CSS separately
await esbuild.build({
  entryPoints: ['src/chat.css'],
  bundle: true,
  outfile: 'dist/chat-bundle.css',
  minify: true,
});

console.log('Build complete: dist/chat-bundle.js + dist/chat-bundle.css');
