import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
  provideAppInitializer,
  provideZonelessChangeDetection,
} from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';

const THEME_KEY = 'msc-muia-2026-theme';

function initTheme(): void {
  const stored = localStorage.getItem(THEME_KEY) as 'dark' | 'light' | null;
  const theme = stored ?? 'dark';
  document.documentElement.classList.remove('dark', 'light');
  document.documentElement.classList.add(theme);
  if (!stored) localStorage.setItem(THEME_KEY, theme);
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideHttpClient(),
    provideRouter(routes),
    provideAppInitializer(initTheme),
  ],
};
