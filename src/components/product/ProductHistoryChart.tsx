import React, { Suspense, lazy, ComponentType } from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ProductHistory } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy load recharts components for better performance (-385KB initial bundle)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyAreaChart = lazy(() => 
  import('recharts').then(m => ({ default: m.AreaChart as ComponentType<any> }))
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyArea = lazy(() => 
  import('recharts').then(m => ({ default: m.Area as ComponentType<any> }))
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyXAxis = lazy(() => 
  import('recharts').then(m => ({ default: m.XAxis as ComponentType<any> }))
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyYAxis = lazy(() => 
  import('recharts').then(m => ({ default: m.YAxis as ComponentType<any> }))
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyCartesianGrid = lazy(() => 
  import('recharts').then(m => ({ default: m.CartesianGrid as ComponentType<any> }))
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyTooltip = lazy(() => 
  import('recharts').then(m => ({ default: m.Tooltip as ComponentType<any> }))
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyLegend = lazy(() => 
  import('recharts').then(m => ({ default: m.Legend as ComponentType<any> }))
);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyResponsiveContainer = lazy(() => 
  import('recharts').then(m => ({ default: m.ResponsiveContainer as ComponentType<any> }))
);

// Chart loading skeleton
const ChartSkeleton = () => (
  <div className="h-[300px] w-full flex items-center justify-center">
    <div className="flex flex-col items-center gap-3">
      <Skeleton className="h-8 w-8 rounded-full" />
      <Skeleton className="h-4 w-32" />
    </div>
  </div>
);

interface ProductHistoryChartProps {
  history: ProductHistory[];
  title?: string;
}

export const ProductHistoryChart: React.FC<ProductHistoryChartProps> = ({ history, title = "Histórico de Vendas e Estoque" }) => {
  if (!history || history.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            Sem dados históricos disponíveis
          </div>
        </CardContent>
      </Card>
    );
  }

  const data = history.map(item => ({
    ...item,
    date: format(new Date(item.collectedAt), 'dd/MM HH:mm', { locale: ptBR }),
    sales: item.salesCount,
    stock: item.stockLevel || 0,
    price: item.price
  }));

  return (
    <Card className="w-full mt-4">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Suspense fallback={<ChartSkeleton />}>
          <div className="h-[300px] w-full">
            <LazyResponsiveContainer width="100%" height="100%">
              <LazyAreaChart
                data={data}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <LazyCartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <LazyXAxis dataKey="date" fontSize={12} />
                <LazyYAxis yAxisId="left" fontSize={12} />
                <LazyYAxis yAxisId="right" orientation="right" fontSize={12} />
                <LazyTooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <LazyLegend />
                <LazyArea 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="sales" 
                  name="Vendas" 
                  stroke="#8884d8" 
                  fill="#8884d8" 
                  fillOpacity={0.3}
                />
                <LazyArea 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="stock" 
                  name="Estoque" 
                  stroke="#82ca9d" 
                  fill="#82ca9d" 
                  fillOpacity={0.3}
                />
              </LazyAreaChart>
            </LazyResponsiveContainer>
          </div>
        </Suspense>
      </CardContent>
    </Card>
  );
};
