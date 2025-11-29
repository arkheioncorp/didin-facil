import { SystemMetricsDashboard } from "@/components/SystemMetricsDashboard";
import DashboardLayout from "@/components/layout/DashboardLayout";

export function MetricsPage() {
  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        <SystemMetricsDashboard />
      </div>
    </DashboardLayout>
  );
}

export default MetricsPage;
