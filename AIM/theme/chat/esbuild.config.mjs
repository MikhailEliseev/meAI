import * as esbuild from 'esbuild';

await esbuild.build({
  entryPoints: ['src/index.jsx'],
  bundle: true,
  outfile: 'dist/chat-bundle.js',
  format: 'iife',
  minify: true,
  external: ['react', 'react-dom', 'react-dom/client'],
  jsx: 'transform',
  loader: { '.css': 'text' },
  banner: {
    js: `var require = (function() {
  var globals = {
    'react': window.React,
    'react-dom': window.ReactDOM,
    'react-dom/client': window.ReactDOM
  };
  return function(name) { return globals[name]; };
})();`,
  },
});

// Also bundle CSS separately
await esbuild.build({
  entryPoints: ['src/chat.css'],
  bundle: true,
  outfile: 'dist/chat-bundle.css',
  minify: true,
});

console.log('Build complete: dist/chat-bundle.js + dist/chat-bundle.css');
