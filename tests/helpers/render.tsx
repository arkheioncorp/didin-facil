/**
 * Custom Render Function for React Testing Library
 * Wraps components with necessary providers
 */
import { ReactElement, ReactNode, createContext, useState } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";

// ============================================
// MOCK THEME PROVIDER
// ============================================

type Theme = "dark" | "light" | "system";

type ThemeProviderState = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
};

const ThemeProviderContext = createContext<ThemeProviderState>({
  theme: "dark",
  setTheme: () => null,
});

interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
}


const ThemeProvider = ({ children, defaultTheme = "dark" }: ThemeProviderProps) => {
  const [theme, setTheme] = useState<Theme>(defaultTheme);

  return (
    <ThemeProviderContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeProviderContext.Provider>
  );
};

// ============================================
// PROVIDERS WRAPPER
// ============================================

interface AllProvidersProps {
  children: ReactNode;
}

const AllProviders = ({ children }: AllProvidersProps) => {
  return (
    <BrowserRouter>
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          {children}
        </TooltipProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

// ============================================
// CUSTOM RENDER
// ============================================

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  route?: string;
  initialState?: Record<string, unknown>;
}

/**
 * Custom render function that wraps component with all necessary providers
 */
const customRender = (
  ui: ReactElement,
  options?: CustomRenderOptions
): ReturnType<typeof render> => {
  const { route = "/", ...renderOptions } = options || {};

  // Set the initial route
  window.history.pushState({}, "Test page", route);

  return render(ui, {
    wrapper: AllProviders,
    ...renderOptions,
  });
};

// ============================================
// EXPORTS
// ============================================

// Re-export everything from testing-library
export * from "@testing-library/react";

// Override render with custom render
export { customRender as render };

// Export userEvent setup
export { default as userEvent } from "@testing-library/user-event";
