/**
 * CRM API Integration
 * 
 * TypeScript API layer for Pipeline and Deal management.
 * Provides type-safe functions for all backend CRM endpoints.
 */

import { api } from "@/lib/api";

// ==================== TYPES ====================

export interface PipelineStage {
    id: string;
    pipeline_id: string;
    name: string;
    color: string;
    probability: number;
    order: number;
    is_won: boolean;
    is_lost: boolean;
    description?: string;
}

export interface Pipeline {
    id: string;
    user_id: string;
    name: string;
    description?: string;
    is_default: boolean;
    is_active: boolean;
    currency: string;
    deal_rotting_days: number;
    created_at: string;
    updated_at: string;
    stages: PipelineStage[];
    // Computed fields
    deal_count?: number;
    total_value?: number;
}

export interface Contact {
    id: string;
    name: string;
    email: string;
    company?: string;
    avatar?: string;
}

export interface Deal {
    id: string;
    user_id: string;
    contact_id: string;
    lead_id?: string | null;
    pipeline_id: string;
    stage_id: string;
    title: string;
    value: number;
    status: "open" | "won" | "lost";
    assigned_to?: string | null;
    expected_close_date?: string | null;
    products: any[];
    tags: string[];
    custom_fields?: Record<string, any>;
    description?: string | null;
    created_at: string;
    updated_at: string;
    // Related data
    contact: Contact;
    // Computed fields
    days_in_stage?: number;
    probability: number;
}

export interface StageMetrics {
    stage_id: string;
    stage_name: string;
    stage_color: string;
    deal_count: number;
    total_value: number;
    weighted_value: number;
    probability: number;
}

export interface PipelineMetrics {
    pipeline_id: string;
    pipeline_name: string;
    total_deals: number;
    total_value: number;
    total_weighted_value: number;
    stage_metrics: StageMetrics[];
    won_deals?: number;
    won_value?: number;
    lost_deals?: number;
    lost_value?: number;
    conversion_rate?: number;
}

export interface PipelineBoard {
    pipeline: Pipeline;
    stages: PipelineStage[];
    deals: Deal[];
}

// Request types
export interface CreatePipelineData {
    name: string;
    description?: string;
    stages?: Array<{
        name: string;
        color?: string;
        probability?: number;
        is_won?: boolean;
        is_lost?: boolean;
    }>;
    currency?: string;
    deal_rotting_days?: number;
    is_default?: boolean;
}

export interface UpdatePipelineData {
    name?: string;
    description?: string;
    stages?: any[];
    currency?: string;
    deal_rotting_days?: number;
    is_active?: boolean;
}

export interface CreateDealData {
    contact_id?: string;
    contact_name?: string;
    contact_email?: string;
    title: string;
    value?: number;
    pipeline_id?: string;
    stage_id?: string;
    lead_id?: string;
    expected_close_date?: string;
    assigned_to?: string;
    products?: any[];
    tags?: string[];
    description?: string;
}

export interface UpdateDealData {
    title?: string;
    description?: string;
    value?: number;
    expected_close_date?: string;
    assigned_to?: string;
    products?: any[];
    tags?: string[];
    custom_fields?: Record<string, any>;
}

export interface MoveDealData {
    stage_id: string;
}

export interface CloseDealData {
    won: boolean;
    reason?: string;
}

// ==================== PIPELINE API ====================

export const pipelineAPI = {
    /**
     * List all pipelines for current user
     */
    list: async (params?: { is_active?: boolean }) => {
        return api.get<Pipeline[]>("/crm/pipelines", { params: params as any });
    },

    /**
     * Get pipeline by ID with stages
     */
    get: async (id: string) => {
        return api.get<Pipeline>(`/crm/pipelines/${id}`);
    },

    /**
     * Get default pipeline (creates if doesn't exist)
     */
    getDefault: async () => {
        return api.get<Pipeline>("/crm/pipelines/default");
    },

    /**
     * Create new pipeline
     */
    create: async (data: CreatePipelineData) => {
        return api.post<Pipeline>("/crm/pipelines", data);
    },

    /**
     * Update pipeline
     */
    update: async (id: string, data: UpdatePipelineData) => {
        return api.patch<Pipeline>(`/crm/pipelines/${id}`, data);
    },

    /**
     * Delete pipeline
     */
    delete: async (id: string) => {
        return api.delete<{ success: boolean; message: string }>(
            `/crm/pipelines/${id}`
        );
    },

    /**
     * Set pipeline as default
     */
    setDefault: async (id: string) => {
        return api.post<{ success: boolean; message: string }>(
            `/crm/pipelines/${id}/default`
        );
    },

    /**
     * Get detailed pipeline metrics
     */
    getMetrics: async (id: string) => {
        return api.get<PipelineMetrics>(`/crm/pipelines/${id}/metrics`);
    },

    /**
     * Add stage to pipeline
     */
    addStage: async (
        pipelineId: string,
        stage: {
            name: string;
            color?: string;
            probability?: number;
            is_won?: boolean;
            is_lost?: boolean;
        },
        position?: number
    ) => {
        return api.post<Pipeline>(
            `/crm/pipelines/${pipelineId}/stages`,
            stage,
            { params: (position !== undefined ? { position } : undefined) as any }
        );
    },

    /**
     * Remove stage from pipeline
     */
    removeStage: async (pipelineId: string, stageId: string) => {
        return api.delete<Pipeline>(
            `/crm/pipelines/${pipelineId}/stages/${stageId}`
        );
    },
};

// ==================== DEAL API ====================

export const dealAPI = {
    /**
     * List deals with optional filters
     */
    list: async (params?: {
        pipeline_id?: string;
        stage_id?: string;
        status?: string;
        contact_id?: string;
        assigned_to?: string;
        min_value?: number;
        max_value?: number;
        tags?: string;
        search?: string;
        page?: number;
        per_page?: number;
        order_by?: string;
        order_dir?: string;
    }) => {
        return api.get<Deal[]>("/crm/deals", { params: params as any });
    },

    /**
     * Get deal by ID
     */
    get: async (id: string) => {
        return api.get<Deal>(`/crm/deals/${id}`);
    },

    /**
     * Get pipeline board (Kanban view)
     */
    getBoard: async (pipelineId: string) => {
        return api.get<PipelineBoard>(`/crm/deals/board/${pipelineId}`);
    },

    /**
     * Get deal statistics
     */
    getStats: async (params?: { pipeline_id?: string }) => {
        return api.get("/crm/deals/stats", { params });
    },

    /**
     * Create new deal
     */
    create: async (data: CreateDealData) => {
        return api.post<Deal>("/crm/deals", data);
    },

    /**
     * Update deal
     */
    update: async (id: string, data: UpdateDealData) => {
        return api.patch<Deal>(`/crm/deals/${id}`, data);
    },

    /**
     * Delete deal
     */
    delete: async (id: string) => {
        return api.delete<{ success: boolean; message: string }>(
            `/crm/deals/${id}`
        );
    },

    /**
     * Move deal to different stage
     */
    move: async (id: string, data: MoveDealData) => {
        return api.post<Deal>(`/crm/deals/${id}/move`, data);
    },

    /**
     * Close deal (win/lose)
     */
    close: async (id: string, data: CloseDealData) => {
        return api.post<{
            success: boolean;
            message: string;
            deal: Deal | null;
        }>(`/crm/deals/${id}/close`, data);
    },

    /**
     * Quick create: create contact + deal in one call
     */
    quickCreate: async (data: {
        email: string;
        deal_title: string;
        deal_value: number;
        contact_name?: string;
        source?: string;
    }) => {
        return api.post<Deal>("/crm/deals/quick", data);
    },
};

// ==================== HELPER FUNCTIONS ====================

/**
 * Calculate weighted value for a deal based on stage probability
 */
export function calculateWeightedValue(
    deal: Deal,
    pipeline: Pipeline
): number {
    const stage = pipeline.stages.find((s) => s.id === deal.stage_id);
    if (!stage) return 0;
    return (deal.value * stage.probability) / 100;
}

/**
 * Calculate days in current stage
 */
export function calculateDaysInStage(deal: Deal): number {
    if (!deal.updated_at) return 0;
    const updated = new Date(deal.updated_at);
    const now = new Date();
    const diff = now.getTime() - updated.getTime();
    return Math.floor(diff / (1000 * 60 * 60 * 24));
}

/**
 * Get color for deal tag
 */
export function getTagColor(tag: string): string {
    const colors: Record<string, string> = {
        Urgente: "bg-red-500/20 text-red-400 border-red-500/30",
        "Hot Lead": "bg-orange-500/20 text-orange-400 border-orange-500/30",
        Enterprise: "bg-purple-500/20 text-purple-400 border-purple-500/30",
        VIP: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
        Novo: "bg-green-500/20 text-green-400 border-green-500/30",
    };
    return colors[tag] || "bg-muted text-muted-foreground border-border";
}

/**
 * Format currency (BRL)
 */
export function formatCurrency(value: number): string {
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
    }).format(value);
}
