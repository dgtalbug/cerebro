// jsdom does not implement ResizeObserver — stub it so component tests pass.
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
