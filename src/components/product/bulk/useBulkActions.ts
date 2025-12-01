import * as React from "react";
import { useBulkActionsStore, useProductSelection } from "@/stores/bulkActionsStore";
import type { Product } from "@/types";
import type { ActionId } from "@/components/product/actions/types";

export interface UseBulkActionsResult {
  selectedProducts: Product[];
  selectedCount: number;
  hasSelection: boolean;
  startBulkAction: (actionId: ActionId, executor: (product: Product) => Promise<void>) => Promise<string>;
  currentJobId: string | null;
}

export const useBulkActions = (): UseBulkActionsResult => {
  const { selectedProducts, hasSelection } = useProductSelection();
  const { createJob, startJob, currentJob } = useBulkActionsStore();
  const [currentJobId, setCurrentJobId] = React.useState<string | null>(null);

  const startBulkAction = React.useCallback(
    async (actionId: ActionId, executor: (product: Product) => Promise<void>) => {
      const jobId = createJob(actionId);
      setCurrentJobId(jobId);
      
      // Start the job asynchronously
      startJob(jobId, executor);
      
      return jobId;
    },
    [createJob, startJob]
  );

  return {
    selectedProducts,
    selectedCount: selectedProducts.length,
    hasSelection,
    startBulkAction,
    currentJobId: currentJob?.id ?? currentJobId,
  };
};
