// @vitest-environment jsdom
//
// The theme module touches `document.documentElement`, `localStorage`,
// and `matchMedia`. We install a Map-backed Storage shim on `window`
// in each beforeEach to dodge a Node 25 / vitest-jsdom interaction
// where Node's experimental Web Storage shadows jsdom's Storage and
// leaves `window.localStorage.clear` undefined.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const STORAGE_KEY = "cerebro-theme";

function installStorageShim(): Storage {
  const backing = new Map<string, string>();
  const shim: Storage = {
    get length() {
      return backing.size;
    },
    clear: () => backing.clear(),
    getItem: (key: string) => backing.get(key) ?? null,
    key: (index: number) => Array.from(backing.keys())[index] ?? null,
    removeItem: (key: string) => {
      backing.delete(key);
    },
    setItem: (key: string, value: string) => {
      backing.set(key, String(value));
    },
  };
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: shim,
  });
  return shim;
}

let storage: Storage;

beforeEach(() => {
  document.documentElement.removeAttribute("data-theme");
  storage = installStorageShim();
  vi.unstubAllGlobals();
  vi.resetModules();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
});

function stubMatchMedia(systemTheme: "dark" | "light" | null): void {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches:
      systemTheme === "dark"
        ? query === "(prefers-color-scheme: dark)"
        : systemTheme === "light"
          ? query === "(prefers-color-scheme: light)"
          : false,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
    onchange: null,
  }));
}

describe("readInitialTheme", () => {
  it("prefers a valid localStorage value", async () => {
    storage.setItem(STORAGE_KEY, "light");
    const { readInitialTheme } = await import("./theme");
    expect(readInitialTheme()).toBe("light");
  });

  it("falls back to prefers-color-scheme: light", async () => {
    stubMatchMedia("light");
    const { readInitialTheme } = await import("./theme");
    expect(readInitialTheme()).toBe("light");
  });

  it("defaults to dark when neither signal is available", async () => {
    stubMatchMedia(null);
    const { readInitialTheme } = await import("./theme");
    expect(readInitialTheme()).toBe("dark");
  });

  it("ignores garbage localStorage values", async () => {
    storage.setItem(STORAGE_KEY, "neon-purple");
    stubMatchMedia(null);
    const { readInitialTheme } = await import("./theme");
    expect(readInitialTheme()).toBe("dark");
  });
});

describe("applyTheme", () => {
  it("writes data-theme on <html> and persists to localStorage", async () => {
    const { applyTheme } = await import("./theme");
    applyTheme("light");

    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(storage.getItem(STORAGE_KEY)).toBe("light");
  });
});

describe("useTheme store", () => {
  it("applies the initial theme to <html> on first import", async () => {
    storage.setItem(STORAGE_KEY, "light");
    await import("./theme");

    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("toggles between dark and light and updates the DOM", async () => {
    storage.setItem(STORAGE_KEY, "dark");
    const { useTheme } = await import("./theme");

    expect(useTheme.getState().theme).toBe("dark");

    useTheme.getState().toggleTheme();
    expect(useTheme.getState().theme).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");

    useTheme.getState().toggleTheme();
    expect(useTheme.getState().theme).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("setTheme writes the value through the store and into localStorage", async () => {
    storage.setItem(STORAGE_KEY, "dark");
    const { useTheme } = await import("./theme");

    useTheme.getState().setTheme("light");

    expect(useTheme.getState().theme).toBe("light");
    expect(storage.getItem(STORAGE_KEY)).toBe("light");
  });
});
