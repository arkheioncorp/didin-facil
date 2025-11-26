/**
 * Sentry Configuration for TikTrend Finder
 * Production error tracking and performance monitoring
 */

import * as Sentry from "@sentry/react";

/**
 * Initialize Sentry for error tracking
 * Call this at the very start of the application
 */
export function initSentry() {
  if (import.meta.env.PROD) {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN,
      environment: import.meta.env.MODE,
      release: `tiktrend-finder@${import.meta.env.VITE_APP_VERSION || "1.0.0"}`,

      // Performance monitoring
      tracesSampleRate: 0.2, // 20% of transactions
      profilesSampleRate: 0.1, // 10% of profiled transactions

      // Session replay
      replaysSessionSampleRate: 0.1, // 10% of sessions
      replaysOnErrorSampleRate: 1.0, // 100% on error

      // Integrations
      integrations: [
        Sentry.browserTracingIntegration({
          // Set `tracePropagationTargets` to control for which URLs distributed tracing should be enabled
          tracePropagationTargets: [
            "localhost",
            /^https:\/\/api\.tiktrend\.com/,
          ],
        }),
        Sentry.replayIntegration({
          // Block elements containing sensitive data
          blockAllMedia: false,
          maskAllText: false,
          maskAllInputs: true,
          block: ["[data-sentry-block]", ".sentry-block"],
          ignore: ["[data-sentry-ignore]", ".sentry-ignore"],
        }),
        Sentry.feedbackIntegration({
          colorScheme: "system",
          showBranding: false,
          buttonLabel: "Reportar Bug",
          submitButtonLabel: "Enviar Feedback",
          formTitle: "Reportar um Problema",
          messagePlaceholder: "Descreva o problema que você encontrou...",
          successMessageText: "Obrigado pelo seu feedback!",
        }),
      ],

      // Filter events
      beforeSend(event, hint) {
        const error = hint.originalException;

        // Don't send errors from development or testing
        if (import.meta.env.DEV || import.meta.env.VITE_TESTING === "true") {
          return null;
        }

        // Filter out known non-critical errors
        if (error instanceof Error) {
          // Network errors that are expected
          if (error.message?.includes("Network request failed")) {
            return null;
          }

          // Cancelled requests
          if (error.message?.includes("AbortError")) {
            return null;
          }

          // Extension errors
          if (error.message?.includes("Extension context invalidated")) {
            return null;
          }
        }

        // Add custom context
        event.extra = {
          ...event.extra,
          userAgent: navigator.userAgent,
          url: window.location.href,
          timestamp: new Date().toISOString(),
        };

        return event;
      },

      // Ignore specific errors
      ignoreErrors: [
        // Browser extensions
        "top.GLOBALS",
        "originalCreateNotification",
        "canvas.contentDocument",
        // Facebook SDK
        "fb_xd_fragment",
        // Chrome extensions
        /chrome-extension/,
        /moz-extension/,
        // Safari extensions
        /safari-extension/,
        // Network errors
        "Network request failed",
        "Failed to fetch",
        // User-cancelled requests
        "AbortError",
        // Tauri-specific
        "Tauri API not available",
      ],

      // Deny URLs (don't track errors from these)
      denyUrls: [
        // Chrome extensions
        /extensions\//i,
        /^chrome:\/\//i,
        /^chrome-extension:\/\//i,
        // Firefox extensions
        /^resource:\/\//i,
        /^moz-extension:\/\//i,
        // Safari extensions
        /^safari-extension:\/\//i,
        // Facebook SDK
        /graph\.facebook\.com/i,
        // Google Analytics
        /connect\.facebook\.net/i,
        /www\.google-analytics\.com/i,
      ],
    });

    console.log("Sentry initialized for production");
  } else {
    console.log("Sentry disabled in development mode");
  }
}

/**
 * Capture a custom error with context
 */
export function captureError(
  error: Error,
  context?: Record<string, unknown>
) {
  if (import.meta.env.PROD) {
    Sentry.withScope((scope) => {
      if (context) {
        Object.entries(context).forEach(([key, value]) => {
          scope.setExtra(key, value);
        });
      }
      Sentry.captureException(error);
    });
  } else {
    console.error("Error captured (dev mode):", error, context);
  }
}

/**
 * Capture a custom message
 */
export function captureMessage(
  message: string,
  level: Sentry.SeverityLevel = "info",
  context?: Record<string, unknown>
) {
  if (import.meta.env.PROD) {
    Sentry.withScope((scope) => {
      if (context) {
        Object.entries(context).forEach(([key, value]) => {
          scope.setExtra(key, value);
        });
      }
      Sentry.captureMessage(message, level);
    });
  } else {
    console.log(`Message captured (dev mode) [${level}]:`, message, context);
  }
}

/**
 * Set user context for error tracking
 */
export function setUser(user: { id: string; email?: string; plan?: string } | null) {
  if (user) {
    Sentry.setUser({
      id: user.id,
      email: user.email,
      subscription: user.plan,
    });
  } else {
    Sentry.setUser(null);
  }
}

/**
 * Add breadcrumb for debugging
 */
export function addBreadcrumb(
  category: string,
  message: string,
  data?: Record<string, unknown>,
  level: Sentry.SeverityLevel = "info"
) {
  Sentry.addBreadcrumb({
    category,
    message,
    data,
    level,
  });
}

/**
 * Start a transaction for performance monitoring
 */
export function startTransaction(
  name: string,
  op: string
): Sentry.Span | undefined {
  return Sentry.startInactiveSpan({
    name,
    op,
  });
}

/**
 * Wrap an async function with Sentry tracing
 */
export async function withSentryTrace<T>(
  name: string,
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  return Sentry.startSpan({ name, op: operation }, async () => {
    return await fn();
  });
}

/**
 * Show feedback dialog to user
 */
export function showFeedbackDialog() {
  // Feedback is handled through the Sentry dashboard configuration
  // or through the Feedback integration initialized in Sentry.init
  console.log('Feedback dialog requested - configure in Sentry dashboard');
}

/**
 * Sentry Error Boundary wrapper for React components
 */
export const SentryErrorBoundary = Sentry.ErrorBoundary;

/**
 * Sentry Profiler wrapper for React components
 */
export const SentryProfiler = Sentry.withProfiler;

export default Sentry;
