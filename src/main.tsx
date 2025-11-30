import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./styles/globals.css";
import "./lib/i18n";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// ============================================
// PWA Service Worker Registration
// ============================================
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });
      
      console.log('[PWA] Service Worker registered:', registration.scope);
      
      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New version available
              console.log('[PWA] New version available');
              
              // Dispatch custom event for UI to show update prompt
              window.dispatchEvent(new CustomEvent('sw-update-available', {
                detail: { registration }
              }));
            }
          });
        }
      });
      
      // Register for periodic background sync if supported
      if ('periodicSync' in registration) {
        try {
          const periodicReg = registration as ServiceWorkerRegistration & {
            periodicSync: { register: (tag: string, options: { minInterval: number }) => Promise<void> }
          };
          await periodicReg.periodicSync.register('check-price-alerts', {
            minInterval: 60 * 60 * 1000 // 1 hour
          });
          console.log('[PWA] Periodic sync registered');
        } catch (error) {
          console.log('[PWA] Periodic sync not available');
        }
      }
      
    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
    }
  });
}

// ============================================
// Push Notification Permission
// ============================================
export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) {
    console.log('[PWA] Notifications not supported');
    return false;
  }
  
  if (Notification.permission === 'granted') {
    return true;
  }
  
  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
  
  return false;
}

// ============================================
// Install Prompt Handler
// ============================================
let deferredPrompt: BeforeInstallPromptEvent | null = null;

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e as BeforeInstallPromptEvent;
  
  // Dispatch event for UI to show install button
  window.dispatchEvent(new CustomEvent('pwa-install-available'));
});

export async function installPWA(): Promise<boolean> {
  if (!deferredPrompt) {
    return false;
  }
  
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  deferredPrompt = null;
  
  return outcome === 'accepted';
}

export function canInstallPWA(): boolean {
  return deferredPrompt !== null;
}

// ============================================
// App Render
// ============================================
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
