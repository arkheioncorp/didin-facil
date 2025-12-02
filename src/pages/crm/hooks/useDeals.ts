/**
 * React Query Hooks for Deals
 * 
 * Custom hooks for managing deal state with automatic caching,
 * optimistic updates, drag-and-drop support, and error handling.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dealAPI, type Deal, type CreateDealData, type UpdateDealData } from "@/lib/api/crm";
import { useToast } from "@/hooks/use-toast";

// Query keys
export const dealKeys = {
    all: ["deals"] as const,
    lists: () => [...dealKeys.all, "list"] as const,
    list: (filters: Record<string, any>) => [...dealKeys.lists(), filters] as const,
    details: () => [...dealKeys.all, "detail"] as const,
    detail: (id: string) => [...dealKeys.details(), id] as const,
    board: (pipelineId: string) => [...dealKeys.all, "board", pipelineId] as const,
    stats: (pipelineId?: string) => [...dealKeys.all, "stats", pipelineId || "all"] as const,
};

/**
 * Fetch deals with optional filters
 */
export function useDeals(filters?: {
    pipeline_id?: string;
    stage_id?: string;
    status?: string;
    search?: string;
}) {
    return useQuery({
        queryKey: dealKeys.list(filters || {}),
        queryFn: async () => {
            const response = await dealAPI.list(filters);
            return response.data;
        },
        staleTime: 1000 * 30, // 30 seconds
    });
}

/**
 * Fetch single deal
 */
export function useDeal(id: string | undefined) {
    return useQuery({
        queryKey: dealKeys.detail(id || ""),
        queryFn: async () => {
            if (!id) throw new Error("Deal ID required");
            const response = await dealAPI.get(id);
            return response.data;
        },
        enabled: !!id,
        staleTime: 1000 * 60,
    });
}

/**
 * Fetch pipeline board (Kanban view)
 */
export function usePipelineBoard(pipelineId: string | undefined) {
    return useQuery({
        queryKey: dealKeys.board(pipelineId || ""),
        queryFn: async () => {
            if (!pipelineId) throw new Error("Pipeline ID required");
            const response = await dealAPI.getBoard(pipelineId);
            return response.data;
        },
        enabled: !!pipelineId,
        staleTime: 1000 * 30,
        refetchInterval: 1000 * 30, // Auto-refresh every 30s
    });
}

/**
 * Fetch deal statistics
 */
export function useDealStats(pipelineId?: string) {
    return useQuery({
        queryKey: dealKeys.stats(pipelineId),
        queryFn: async () => {
            const response = await dealAPI.getStats(
                pipelineId ? { pipeline_id: pipelineId } : undefined
            );
            return response.data;
        },
        staleTime: 1000 * 60,
    });
}

/**
 * Create new deal
 */
export function useCreateDeal() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async (data: CreateDealData) => {
            const response = await dealAPI.create(data);
            return response.data;
        },
        onSuccess: (newDeal) => {
            // Invalidate all deal queries
            queryClient.invalidateQueries({ queryKey: dealKeys.all });

            toast({
                title: "Deal criado!",
                description: `"${newDeal.title}" foi adicionado ao pipeline.`,
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro ao criar deal",
                description: error?.response?.data?.detail || "Não foi possível criar o deal.",
                variant: "destructive",
            });
        },
    });
}

/**
 * Update deal
 */
export function useUpdateDeal() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async ({ id, data }: { id: string; data: UpdateDealData }) => {
            const response = await dealAPI.update(id, data);
            return response.data;
        },
        onSuccess: (updatedDeal) => {
            // Invalidate specific deal and lists
            queryClient.invalidateQueries({ queryKey: dealKeys.detail(updatedDeal.id) });
            queryClient.invalidateQueries({ queryKey: dealKeys.lists() });
            queryClient.invalidateQueries({ queryKey: dealKeys.board(updatedDeal.pipeline_id) });

            toast({
                title: "Deal atualizado!",
                description: `"${updatedDeal.title}" foi atualizado.`,
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro ao atualizar",
                description: error?.response?.data?.detail || "Não foi possível atualizar o deal.",
                variant: "destructive",
            });
        },
    });
}

/**
 * Delete deal
 */
export function useDeleteDeal() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async (id: string) => {
            const response = await dealAPI.delete(id);
            return response.data;
        },
        onSuccess: (_, deletedId) => {
            // Remove from cache
            queryClient.removeQueries({ queryKey: dealKeys.detail(deletedId) });
            queryClient.invalidateQueries({ queryKey: dealKeys.lists() });
            queryClient.invalidateQueries({ queryKey: dealKeys.all });

            toast({
                title: "Deal removido",
                description: "O deal foi deletado com sucesso.",
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro ao deletar",
                description: error?.response?.data?.detail || "Não foi possível deletar o deal.",
                variant: "destructive",
            });
        },
    });
}

/**
 * Move deal to different stage (drag & drop)
 */
export function useMoveDeal() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async ({ id, stage_id }: { id: string; stage_id: string }) => {
            const response = await dealAPI.move(id, { stage_id });
            return response.data;
        },
        // Optimistic update for instant UI feedback
        onMutate: async ({ id, stage_id }) => {
            // Cancel outgoing refetches
            await queryClient.cancelQueries({ queryKey: dealKeys.all });

            // Snapshot previous value
            const previousDeals = queryClient.getQueryData(dealKeys.lists());

            // Optimistically update cache
            queryClient.setQueriesData(
                { queryKey: dealKeys.lists() },
                (old: Deal[] | undefined) => {
                    if (!old) return old;
                    return old.map((deal) =>
                        deal.id === id
                            ? { ...deal, stage_id, days_in_stage: 0 }
                            : deal
                    );
                }
            );

            return { previousDeals };
        },
        onSuccess: (updatedDeal) => {
            // Invalidate to sync with server
            queryClient.invalidateQueries({ queryKey: dealKeys.all });

            toast({
                title: "Deal movido!",
                description: `"${updatedDeal.title}" foi movido para o novo estágio.`,
            });
        },
        onError: (error: any, _variables, context) => {
            // Rollback on error
            if (context?.previousDeals) {
                queryClient.setQueryData(dealKeys.lists(), context.previousDeals);
            }

            toast({
                title: "Erro ao mover deal",
                description: error?.response?.data?.detail || "Não foi possível mover o deal.",
                variant: "destructive",
            });
        },
    });
}

/**
 * Mark deal as won
 */
export function useWinDeal() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async (id: string) => {
            const response = await dealAPI.close(id, { won: true });
            return response.data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: dealKeys.all });

            toast({
                title: "🎉 Deal ganho!",
                description: data.deal ? `"${data.deal.title}" foi marcado como ganho!` : "Deal marcado como ganho!",
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro",
                description: error?.response?.data?.detail || "Não foi possível marcar como ganho.",
                variant: "destructive",
            });
        },
    });
}

/**
 * Mark deal as lost
 */
export function useLoseDeal() {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    return useMutation({
        mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
            const response = await dealAPI.close(id, { won: false, reason });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: dealKeys.all });

            toast({
                title: "Deal perdido",
                description: "O deal foi marcado como perdido.",
            });
        },
        onError: (error: any) => {
            toast({
                title: "Erro",
                description: error?.response?.data?.detail || "Não foi possível marcar como perdido.",
                variant: "destructive",
            });
        },
    });
}
