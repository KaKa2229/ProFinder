const CACHE_NAME = 'profinder-cache-v2';
const STATIC_ASSETS = [
  '/offline',
  '/static/img/icons/icon-192x192.png',
  '/static/img/icons/icon-512x512.png'
];

// Instala e faz pre-cache dos assets essenciais
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
  );
});

// Ativa e limpa caches antigos
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })
  );
  return self.clients.claim();
});

// Estratégia: Network first para navegação, cache first para assets estáticos
self.addEventListener('fetch', event => {
  const { request } = event;

  // Navegação: tenta rede, fallback para offline
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Guarda uma cópia da página no cache
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match('/offline'))
    );
    return;
  }

  // Assets estáticos: tenta cache primeiro, depois rede
  if (request.url.includes('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          return response;
        });
      })
    );
  }
});
