import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const Pipeline = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Pipeline de Vendas</h1>
      <Card>
        <CardHeader>
          <CardTitle>Kanban de Vendas</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Em breve: Visualização Kanban do seu funil de vendas.</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default Pipeline;
