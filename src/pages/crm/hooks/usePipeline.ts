/**
 * React Query Hooks for Pipelines
 * 
 * Custom hooks for managing pipeline state with automatic caching,
 * optimistic updates, and error handling.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pipelineAPI, type CreatePipelineData, type UpdatePipelineData } from "@/lib/api/crm";
import { useToast } from "@/hooks/use-toast";

// Query keys
export const pipelineKeys = {
    all: ["pipelines"] as const,
    lists: () => [...pipelineKeys.all, "list"] as const,
    list: (filters: Record<string, any>) => [...pipelineKeys.lists(), filters] as const,
    details: () => [...pipelineKeys.all, "detail"] as const,
    detail: (id: string) => [...pipelineKeys.details(), id] as const,
    metrics: (id: string) => [...pipelineKeys.detail(id), "metrics"] as const,
};

/**
 * Fetch all pipelines
 */
export function usePipelines(params?: { is_active?: boolean }) {
    return useQuery({
        queryKey: pipelineKeys.list(params || {}),
        queryFn: async () => {
            const response = await pipelineAPI.list(params);
            return response.data;
        },
        staleTime: 1000 * 60 * 5, // 5 minutes
    });
}

/**
 * Fetch single pipeline with stages
 */
export function usePipeline(id: string | undefined) {
    return useQuery({
        queryKey: pipelineKeys.detail(id || ""),
        queryFn: async () => {
            if (!id) throw new Error("Pipeline ID required");
            const response = await pipelineAPI.get(id);
            return response.data;
        },
        enabled: !!id,
        staleTime: 1000 * 60 * 5,
    });
}

/**
 * Fetch default pipeline
 */
export function useDefaultPipeline() {
    return useQuery({
        queryKey: [...pipelineKeys.all, "default"],
        queryFn: async () => {
            const response = await pipelineAPI.getDefault();
            return response.data;
        },
        staleTime: 1000 * 60 * 10,
    });
}

/**
 * Fetch pipeline metrics
 */
export function usePipelineMetrics(id: string | undefined) {
    return useQuery({
        queryKey: pipelineKeys.metrics(id || ""),
        queryFn: async () => {
            if (!id) throw new Error("Pipeline ID required");
            const response = await pipelineAPI.getMetrics(id);
            return response.data;
        },
        enabled: !!id,
        staleTime: 1000 * 30, // 30 seconds (metrics change frequently)
    });
}

/**
 * Create new pipeline
 */
export function useCreatePipeline() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async (data: CreatePipelineData) => {
            const response = await pipelineAPI.create(data);
            return response.data;
        },
        onSuccess: (newPipeline) => {
            // Invalidate all pipeline queries
            queryClient.invalidateQueries({ queryKey: pipelineKeys.all });

            toast({
                title: "Pipeline criado!",
                description: `"${newPipeline.name}" foi criado com sucesso.`,
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro ao criar pipeline",
                description: error?.response?.data?.detail || "Não foi possível criar o pipeline.",
                variant: "destructive",
            });
        },
    });
}

/**
 * Update pipeline
 */
export function useUpdatePipeline() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async ({ id, data }: { id: string; data: UpdatePipelineData }) => {
            const response = await pipelineAPI.update(id, data);
            return response.data;
        },
        onSuccess: (updatedPipeline) => {
            // Invalidate specific pipeline and list
            queryClient.invalidateQueries({ queryKey: pipelineKeys.detail(updatedPipeline.id) });
            queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() });

            toast({
                title: "Pipeline atualizado!",
                description: `"${updatedPipeline.name}" foi atualizado.`,
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro ao atualizar",
                description: error?.response?.data?.detail || "Não foi possível atualizar o pipeline.",
                variant: "destructive",
            });
        },
    });
}

/**
 * Delete pipeline
 */
export function useDeletePipeline() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async (id: string) => {
            const response = await pipelineAPI.delete(id);
            return response.data;
        },
        onSuccess: (_, deletedId) => {
            // Remove from cache
            queryClient.removeQueries({ queryKey: pipelineKeys.detail(deletedId) });
            queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() });

            toast({
                title: "Pipeline removido",
                description: "O pipeline foi deletado com sucesso.",
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro ao deletar",
                description: error?.response?.data?.detail || "Não foi possível deletar o pipeline.",
                variant: "destructive",
            });
        },
    });
}

/**
 * Set pipeline as default
 */
export function useSetDefaultPipeline() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async (id: string) => {
            const response = await pipelineAPI.setDefault(id);
            return response.data;
        },
        onSuccess: () => {
            // Invalidate all pipelines to update is_default flags
            queryClient.invalidateQueries({ queryKey: pipelineKeys.all });

            toast({
                title: "Pipeline padrão definido",
                description: "Este pipeline agora é o padrão.",
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro",
                description: error?.response?.data?.detail || "Não foi possível definir como padrão.",
                variant: "destructive",
            });
        },
    });
}
