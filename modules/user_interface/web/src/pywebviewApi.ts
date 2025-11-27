// src/pywebviewApi.ts
import type { PywebviewApi } from "./types/data_types";

export function getPywebviewApi(): PywebviewApi | null {
  if (window.pywebview && window.pywebview.api) {
    return window.pywebview.api;
  }
  // Optional: return a mock in dev if you want
  console.warn("pywebview api not available (running in plain browser?)");
  return null;
}
