import React from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ProductHistory } from '@/types';

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
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="date" fontSize={12} />
              <YAxis yAxisId="left" fontSize={12} />
              <YAxis yAxisId="right" orientation="right" fontSize={12} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Legend />
              <Area 
                yAxisId="left"
                type="monotone" 
                dataKey="sales" 
                name="Vendas" 
                stroke="#8884d8" 
                fill="#8884d8" 
                fillOpacity={0.3}
              />
              <Area 
                yAxisId="right"
                type="monotone" 
                dataKey="stock" 
                name="Estoque" 
                stroke="#82ca9d" 
                fill="#82ca9d" 
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};
