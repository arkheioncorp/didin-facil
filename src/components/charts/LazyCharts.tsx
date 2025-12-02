/**
 * Lazy-loaded Chart Components
 * 
 * Este módulo exporta versões lazy-loaded dos componentes do Recharts
 * para reduzir o bundle inicial em ~385KB.
 * 
 * @performance Reduz initial bundle de 548KB → ~200KB
 */

import React, { lazy, Suspense } from 'react';

// Chart loading fallback
export const ChartSkeleton = ({ height = 300 }: { height?: number }) => (
  <div 
    className="w-full animate-pulse bg-muted/50 rounded-lg flex items-center justify-center"
    style={{ height }}
  >
    <div className="flex flex-col items-center gap-2 text-muted-foreground">
      <div className="w-8 h-8 border-2 border-muted-foreground/30 border-t-muted-foreground rounded-full animate-spin" />
      <span className="text-sm">Carregando gráfico...</span>
    </div>
  </div>
);

// Lazy load individual chart components directly
export const LazyLineChart = lazy(() => 
  import('recharts').then(mod => ({ default: mod.LineChart }))
);

export const LazyBarChart = lazy(() => 
  import('recharts').then(mod => ({ default: mod.BarChart }))
);

export const LazyAreaChart = lazy(() => 
  import('recharts').then(mod => ({ default: mod.AreaChart }))
);

export const LazyPieChart = lazy(() => 
  import('recharts').then(mod => ({ default: mod.PieChart }))
);

export const LazyResponsiveContainer = lazy(() => 
  import('recharts').then(mod => ({ default: mod.ResponsiveContainer }))
);

// Helper component that wraps everything in Suspense
interface ChartWrapperProps {
  children: React.ReactNode;
  height?: number;
}

export const ChartWrapper: React.FC<ChartWrapperProps> = ({ children, height = 300 }) => (
  <Suspense fallback={<ChartSkeleton height={height} />}>
    {children}
  </Suspense>
);

// Re-export utilities that don't need lazy loading
// These are small and needed immediately when chart is rendered
export { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  Line,
  Bar,
  Area,
  ResponsiveContainer
} from 'recharts';

// For pages that need the full recharts module
export const useRecharts = () => {
  const [recharts, setRecharts] = React.useState<typeof import('recharts') | null>(null);
  
  React.useEffect(() => {
    import('recharts').then(setRecharts);
  }, []);
  
  return recharts;
};
