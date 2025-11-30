/// <reference lib="webworker" />

/**
 * Service Worker para PWA do Didin Fácil
 * 
 * Funcionalidades:
 * - Cache de assets estáticos
 * - Offline-first para páginas visitadas
 * - Background sync para agendamentos
 * - Push notifications
 */

const CACHE_NAME = 'didin-facil-v1';
const STATIC_CACHE = 'didin-static-v1';
const DYNAMIC_CACHE = 'didin-dynamic-v1';
const API_CACHE = 'didin-api-v1';

// Assets estáticos para cache
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/offline.html',
  // Assets serão adicionados pelo build
];

// Rotas de API para cache
const API_ROUTES = [
  '/api/v1/products',
  '/api/v1/categories',
  '/api/v1/user/profile',
];

// Instalação do Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Ativação - limpar caches antigos
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker');
  
  const cacheWhitelist = [STATIC_CACHE, DYNAMIC_CACHE, API_CACHE];
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (!cacheWhitelist.includes(cacheName)) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Interceptar requisições
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Ignorar extensões do Chrome e requests externos
  if (url.protocol === 'chrome-extension:' || 
      !url.origin.includes(self.location.origin)) {
    return;
  }
  
  // Estratégia para API
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
    return;
  }
  
  // Estratégia para assets estáticos
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirstStrategy(request));
    return;
  }
  
  // Estratégia para navegação (páginas)
  if (request.mode === 'navigate') {
    event.respondWith(networkFirstWithOffline(request));
    return;
  }
  
  // Default: Network first
  event.respondWith(networkFirstStrategy(request));
});

/**
 * Verifica se é um asset estático
 */
function isStaticAsset(pathname) {
  const staticExtensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf'];
  return staticExtensions.some(ext => pathname.endsWith(ext));
}

/**
 * Estratégia: Cache First
 * Primeiro tenta cache, depois network
 */
async function cacheFirstStrategy(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, response.clone());
    return response;
  } catch (error) {
    console.error('[SW] Fetch failed:', error);
    throw error;
  }
}

/**
 * Estratégia: Network First
 * Primeiro tenta network, fallback para cache
 */
async function networkFirstStrategy(request) {
  try {
    const response = await fetch(request);
    
    // Cache a resposta se for válida
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    throw error;
  }
}

/**
 * Estratégia: Network First com fallback offline
 */
async function networkFirstWithOffline(request) {
  try {
    const response = await fetch(request);
    
    // Cache páginas visitadas
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // Tentar cache
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    
    // Fallback para página offline
    const offlinePage = await caches.match('/offline.html');
    if (offlinePage) {
      return offlinePage;
    }
    
    // HTML mínimo de offline
    return new Response(
      `<!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Offline - Didin Fácil</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: #1a1a2e;
            color: white;
          }
          .container {
            text-align: center;
            padding: 2rem;
          }
          .icon { font-size: 4rem; margin-bottom: 1rem; }
          h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
          p { color: #a0a0a0; margin-bottom: 1.5rem; }
          button {
            background: #6366f1;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            cursor: pointer;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="icon">📡</div>
          <h1>Você está offline</h1>
          <p>Verifique sua conexão e tente novamente</p>
          <button onclick="location.reload()">Tentar novamente</button>
        </div>
      </body>
      </html>`,
      { headers: { 'Content-Type': 'text/html' } }
    );
  }
}

// ============================================
// BACKGROUND SYNC
// ============================================

self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-scheduled-posts') {
    event.waitUntil(syncScheduledPosts());
  }
  
  if (event.tag === 'sync-favorites') {
    event.waitUntil(syncFavorites());
  }
});

async function syncScheduledPosts() {
  try {
    const db = await openDB();
    const posts = await db.getAll('pending-posts');
    
    for (const post of posts) {
      try {
        await fetch('/api/v1/scheduler/posts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(post)
        });
        
        await db.delete('pending-posts', post.id);
      } catch (error) {
        console.error('[SW] Failed to sync post:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

async function syncFavorites() {
  // Implementar sync de favoritos
}

// ============================================
// PUSH NOTIFICATIONS
// ============================================

self.addEventListener('push', (event) => {
  console.log('[SW] Push received');
  
  let data = {
    title: 'Didin Fácil',
    body: 'Nova notificação',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge.png'
  };
  
  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }
  
  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    vibrate: [100, 50, 100],
    data: data.data || {},
    actions: data.actions || [
      { action: 'view', title: 'Ver' },
      { action: 'dismiss', title: 'Dispensar' }
    ],
    tag: data.tag || 'didin-notification',
    renotify: true,
    requireInteraction: data.requireInteraction || false
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');
  
  event.notification.close();
  
  const data = event.notification.data;
  let url = '/';
  
  if (data && data.url) {
    url = data.url;
  }
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.matchAll({ type: 'window' })
        .then((clientList) => {
          // Se já tem uma janela aberta, focar nela
          for (const client of clientList) {
            if (client.url === url && 'focus' in client) {
              return client.focus();
            }
          }
          // Senão, abrir nova janela
          if (clients.openWindow) {
            return clients.openWindow(url);
          }
        })
    );
  }
});

// ============================================
// PERIODIC BACKGROUND SYNC
// ============================================

self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'check-price-alerts') {
    event.waitUntil(checkPriceAlerts());
  }
  
  if (event.tag === 'sync-analytics') {
    event.waitUntil(syncAnalytics());
  }
});

async function checkPriceAlerts() {
  try {
    const response = await fetch('/api/v1/alerts/check');
    const alerts = await response.json();
    
    for (const alert of alerts.triggered) {
      await self.registration.showNotification('🔔 Alerta de Preço!', {
        body: `${alert.product} baixou para R$ ${alert.price}`,
        icon: '/icons/icon-192x192.png',
        data: { url: alert.url },
        tag: `price-alert-${alert.id}`
      });
    }
  } catch (error) {
    console.error('[SW] Failed to check price alerts:', error);
  }
}

async function syncAnalytics() {
  // Enviar analytics pendentes
}

// ============================================
// MESSAGE HANDLING
// ============================================

self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(DYNAMIC_CACHE)
        .then((cache) => cache.addAll(event.data.urls))
    );
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});

// ============================================
// HELPER: IndexedDB
// ============================================

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('didin-offline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('pending-posts')) {
        db.createObjectStore('pending-posts', { keyPath: 'id' });
      }
      
      if (!db.objectStoreNames.contains('pending-favorites')) {
        db.createObjectStore('pending-favorites', { keyPath: 'id' });
      }
    };
  });
}
