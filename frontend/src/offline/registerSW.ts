/**
 * Service worker registration for offline static caching.
 *
 * The worker is served from the API root (`/sw.js`) rather than from the SPA
 * mount at `/app`, so its scope also covers the hashed bundles under `/assets`.
 */

export const registerServiceWorker = (): void => {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
  if (!import.meta.env.PROD) return;

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .catch((err) => console.warn('Service worker registration failed:', err));
  });
};
