// global.d.ts
import type { PywebviewApi } from "./types/data_types";

declare global {
  interface Window {
    pywebview?: {
      api?: PywebviewApi;
    };
  }
}

export {};
