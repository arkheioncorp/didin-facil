import { SystemMetricsDashboard } from "@/components/SystemMetricsDashboard";
import { Layout } from "@/components/layout/Layout";

export function MetricsPage() {
  return (
    <Layout>
      <div className="container mx-auto py-6">
        <SystemMetricsDashboard />
      </div>
    </Layout>
  );
}

export default MetricsPage;
