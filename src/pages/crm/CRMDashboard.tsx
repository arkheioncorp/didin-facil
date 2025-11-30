import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const CRMDashboard = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">CRM & Vendas</h1>
      <Card>
        <CardHeader>
          <CardTitle>Gestão de Leads</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Em breve: Pipeline de vendas e gestão de contatos.</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default CRMDashboard;
