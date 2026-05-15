// Polyfills that must be loaded before any other code
class ResizeObserverPolyfill {
  observe() {}
  unobserve() {}
  disconnect() {}
}

Object.defineProperty(global, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: ResizeObserverPolyfill,
})

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: ResizeObserverPolyfill,
})
