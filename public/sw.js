// Cache only the interface. Never cache audio, transcripts, or API responses.
const CACHE = 'schwatz-shell-v15';
const SHELL = ['/', '/style.css?v=15', '/app.js?v=15', '/listening-ui.js?v=15', '/icon.svg', '/manifest.webmanifest'];
self.addEventListener('install', event => { event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener('activate', event => { event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('schwatz-shell-') && key !== CACHE).map(key => caches.delete(key))))); self.clients.claim(); });
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin || !SHELL.includes(url.pathname + url.search)) return;
  event.respondWith(fetch(event.request, { cache: 'no-cache' }).then(response => { if (response.ok) { const copy = response.clone(); caches.open(CACHE).then(cache => cache.put(event.request, copy)); } return response; }).catch(() => caches.match(event.request)));
});
