/**
 * Debug Utilities for TikTrend Finder
 * Professional debugging and logging tools
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: unknown;
  stack?: string;
}

// In-memory log buffer for debugging
const logBuffer: LogEntry[] = [];
const MAX_LOG_BUFFER = 500;

// Debug mode detection
const isDebugMode = (): boolean => {
  return (
    import.meta.env.DEV ||
    import.meta.env.VITE_DEBUG === 'true' ||
    localStorage.getItem('debug_mode') === 'true'
  );
};

// Color codes for console
const COLORS = {
  debug: '#888888',
  info: '#2196F3',
  warn: '#FF9800',
  error: '#F44336',
};

/**
 * Create a scoped logger for a specific category
 */
export function createLogger(category: string) {
  const log = (level: LogLevel, message: string, data?: unknown) => {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      data,
    };

    // Add to buffer
    logBuffer.push(entry);
    if (logBuffer.length > MAX_LOG_BUFFER) {
      logBuffer.shift();
    }

    // Console output in debug mode
    if (isDebugMode()) {
      const style = `color: ${COLORS[level]}; font-weight: bold;`;
      const prefix = `[${entry.timestamp}] [${level.toUpperCase()}] [${category}]`;
      
      if (data !== undefined) {
        console.groupCollapsed(`%c${prefix} ${message}`, style);
        console.log('Data:', data);
        console.groupEnd();
      } else {
        console.log(`%c${prefix} ${message}`, style);
      }
    }

    // Send errors to Sentry in production
    if (level === 'error' && import.meta.env.PROD) {
      import('./sentry').then(({ captureMessage, addBreadcrumb }) => {
        addBreadcrumb(category, message, data as Record<string, unknown>, level);
        if (data instanceof Error) {
          import('./sentry').then(({ captureError }) => {
            captureError(data, { category, message });
          });
        } else {
          captureMessage(message, 'error', { category, data });
        }
      });
    }

    return entry;
  };

  return {
    debug: (message: string, data?: unknown) => log('debug', message, data),
    info: (message: string, data?: unknown) => log('info', message, data),
    warn: (message: string, data?: unknown) => log('warn', message, data),
    error: (message: string, data?: unknown) => log('error', message, data),
  };
}

/**
 * Performance timing utility
 */
export class PerformanceTimer {
  private startTime: number;
  private marks: Map<string, number> = new Map();
  private logger = createLogger('Performance');

  constructor(private name: string) {
    this.startTime = performance.now();
    this.logger.debug(`Timer started: ${name}`);
  }

  mark(label: string) {
    const now = performance.now();
    const elapsed = now - this.startTime;
    this.marks.set(label, elapsed);
    this.logger.debug(`Mark "${label}": ${elapsed.toFixed(2)}ms`);
  }

  end(): number {
    const totalTime = performance.now() - this.startTime;
    this.logger.info(`Timer "${this.name}" completed: ${totalTime.toFixed(2)}ms`, {
      marks: Object.fromEntries(this.marks),
    });
    return totalTime;
  }
}

/**
 * Measure async function execution time
 */
export async function measureAsync<T>(
  name: string,
  fn: () => Promise<T>
): Promise<T> {
  const timer = new PerformanceTimer(name);
  try {
    const result = await fn();
    timer.end();
    return result;
  } catch (error) {
    timer.mark('error');
    timer.end();
    throw error;
  }
}

/**
 * Debug panel state and actions
 */
class DebugPanel {
  private isVisible = false;
  private panelElement: HTMLElement | null = null;

  toggle() {
    if (this.isVisible) {
      this.hide();
    } else {
      this.show();
    }
  }

  show() {
    if (!isDebugMode()) {
      console.warn('Debug panel is only available in debug mode');
      return;
    }

    if (this.panelElement) {
      this.panelElement.style.display = 'block';
      this.isVisible = true;
      return;
    }

    this.createPanel();
    this.isVisible = true;
  }

  hide() {
    if (this.panelElement) {
      this.panelElement.style.display = 'none';
      this.isVisible = false;
    }
  }

  private createPanel() {
    const panel = document.createElement('div');
    panel.id = 'debug-panel';
    panel.style.cssText = `
      position: fixed;
      bottom: 10px;
      right: 10px;
      width: 400px;
      max-height: 500px;
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 8px;
      padding: 10px;
      font-family: 'Monaco', 'Consolas', monospace;
      font-size: 12px;
      color: #fff;
      z-index: 99999;
      overflow: auto;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    `;

    panel.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <strong style="color: #4CAF50;">🐛 Debug Panel</strong>
        <button id="debug-panel-close" style="background: none; border: none; color: #888; cursor: pointer; font-size: 18px;">&times;</button>
      </div>
      <div id="debug-tabs" style="display: flex; gap: 10px; margin-bottom: 10px;">
        <button class="debug-tab active" data-tab="logs">Logs</button>
        <button class="debug-tab" data-tab="state">State</button>
        <button class="debug-tab" data-tab="network">Network</button>
        <button class="debug-tab" data-tab="perf">Performance</button>
      </div>
      <div id="debug-content" style="max-height: 400px; overflow: auto;">
        <div id="debug-logs" class="debug-pane"></div>
        <div id="debug-state" class="debug-pane" style="display: none;"></div>
        <div id="debug-network" class="debug-pane" style="display: none;"></div>
        <div id="debug-perf" class="debug-pane" style="display: none;"></div>
      </div>
    `;

    document.body.appendChild(panel);
    this.panelElement = panel;

    // Event listeners
    panel.querySelector('#debug-panel-close')?.addEventListener('click', () => this.hide());
    panel.querySelectorAll('.debug-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        this.switchTab(target.dataset.tab || 'logs');
      });
    });

    // Style tabs
    const style = document.createElement('style');
    style.textContent = `
      .debug-tab {
        background: #333;
        border: none;
        color: #888;
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
      }
      .debug-tab.active {
        background: #4CAF50;
        color: #fff;
      }
      .debug-pane {
        font-size: 11px;
      }
      .log-entry {
        padding: 4px;
        border-bottom: 1px solid #333;
      }
      .log-debug { color: #888; }
      .log-info { color: #2196F3; }
      .log-warn { color: #FF9800; }
      .log-error { color: #F44336; }
    `;
    document.head.appendChild(style);

    // Update logs
    this.updateLogs();
  }

  private switchTab(tabName: string) {
    if (!this.panelElement) return;

    this.panelElement.querySelectorAll('.debug-tab').forEach(tab => {
      tab.classList.remove('active');
    });
    this.panelElement.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');

    this.panelElement.querySelectorAll('.debug-pane').forEach(pane => {
      (pane as HTMLElement).style.display = 'none';
    });
    const activePane = this.panelElement.querySelector(`#debug-${tabName}`);
    if (activePane) {
      (activePane as HTMLElement).style.display = 'block';
    }

    // Update content based on tab
    switch (tabName) {
      case 'logs':
        this.updateLogs();
        break;
      case 'state':
        this.updateState();
        break;
      case 'perf':
        this.updatePerformance();
        break;
    }
  }

  private updateLogs() {
    const logsPane = this.panelElement?.querySelector('#debug-logs');
    if (!logsPane) return;

    logsPane.innerHTML = logBuffer
      .slice(-50)
      .reverse()
      .map(entry => `
        <div class="log-entry log-${entry.level}">
          <span style="color: #666;">${entry.timestamp.split('T')[1].slice(0, 8)}</span>
          <span style="color: #888;">[${entry.category}]</span>
          ${entry.message}
        </div>
      `)
      .join('');
  }

  private updateState() {
    const statePane = this.panelElement?.querySelector('#debug-state');
    if (!statePane) return;

    // Get Zustand stores state
    const state = {
      localStorage: Object.keys(localStorage).reduce((acc, key) => {
        try {
          acc[key] = JSON.parse(localStorage.getItem(key) || '');
        } catch {
          acc[key] = localStorage.getItem(key);
        }
        return acc;
      }, {} as Record<string, unknown>),
    };

    statePane.innerHTML = `<pre style="white-space: pre-wrap;">${JSON.stringify(state, null, 2)}</pre>`;
  }

  private updatePerformance() {
    const perfPane = this.panelElement?.querySelector('#debug-perf');
    if (!perfPane) return;

    const entries = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const memory = (performance as unknown as { memory?: { usedJSHeapSize: number; totalJSHeapSize: number } }).memory;

    perfPane.innerHTML = `
      <div>
        <strong>Navigation Timing</strong>
        <div>DOM Content Loaded: ${entries?.domContentLoadedEventEnd?.toFixed(0) || 'N/A'}ms</div>
        <div>Load Event: ${entries?.loadEventEnd?.toFixed(0) || 'N/A'}ms</div>
        <div>DOM Interactive: ${entries?.domInteractive?.toFixed(0) || 'N/A'}ms</div>
      </div>
      ${memory ? `
        <div style="margin-top: 10px;">
          <strong>Memory</strong>
          <div>Used: ${(memory.usedJSHeapSize / 1048576).toFixed(2)} MB</div>
          <div>Total: ${(memory.totalJSHeapSize / 1048576).toFixed(2)} MB</div>
        </div>
      ` : ''}
    `;
  }
}

// Export singleton debug panel
export const debugPanel = new DebugPanel();

// Global debug commands
if (typeof window !== 'undefined') {
  (window as unknown as { __debug: object }).__debug = {
    panel: debugPanel,
    logs: () => console.table(logBuffer.slice(-20)),
    clearLogs: () => logBuffer.length = 0,
    enableDebug: () => localStorage.setItem('debug_mode', 'true'),
    disableDebug: () => localStorage.removeItem('debug_mode'),
  };
}

// Keyboard shortcut for debug panel
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', (e) => {
    // Ctrl+Shift+D to toggle debug panel
    if (e.ctrlKey && e.shiftKey && e.key === 'D') {
      e.preventDefault();
      debugPanel.toggle();
    }
  });
}

export { isDebugMode, logBuffer };
