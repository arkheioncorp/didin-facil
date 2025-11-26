type EventName = 
  | 'app_opened'
  | 'search_performed'
  | 'product_viewed'
  | 'copy_generated'
  | 'favorite_added'
  | 'favorite_removed'
  | 'export_performed';

interface AnalyticsProperties {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

class Analytics {
  private static instance: Analytics;
  private initialized = false;
  private isDev = import.meta.env.DEV;

  private constructor() {}

  public static getInstance(): Analytics {
    if (!Analytics.instance) {
      Analytics.instance = new Analytics();
    }
    return Analytics.instance;
  }

  public init(apiKey?: string) {
    if (this.initialized) return;
    
    if (apiKey) {
      // Initialize PostHog here when package is available
      // posthog.init(apiKey, { api_host: 'https://app.posthog.com' });
      console.log('[Analytics] Initialized with API Key');
    } else {
      console.log('[Analytics] Initialized in local mode');
    }
    
    this.initialized = true;
    this.track('app_opened');
  }

  public track(event: EventName, properties?: AnalyticsProperties) {
    if (!this.initialized) {
      console.warn('[Analytics] Not initialized');
      return;
    }

    if (this.isDev) {
      console.log(`[Analytics] Track: ${event}`, properties);
    }

    // if (window.posthog) {
    //   window.posthog.capture(event, properties);
    // }
  }

  public identify(userId: string, properties?: AnalyticsProperties) {
    if (this.isDev) {
      console.log(`[Analytics] Identify: ${userId}`, properties);
    }
    
    // if (window.posthog) {
    //   window.posthog.identify(userId, properties);
    // }
  }
}

export const analytics = Analytics.getInstance();
