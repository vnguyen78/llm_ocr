import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1/claims';
// Derive the generic base URL (strip /claims if present)
export const BASE_URL = API_URL.endsWith('/claims') ? API_URL.slice(0, -7) : API_URL;

const client = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface ReviewCorrection {
    tile_id: string;
    field_name: string;
    new_value: string | number;
}

export interface ReviewPayload {
    corrections: ReviewCorrection[];
    confirm_with_issues?: boolean;
    approval_note?: string;
}

export interface ApplicationResponse {
    id: string;
    name?: string;
    status: string;
    created_at: string;
    documents?: any[]; // We can refine this type later if needed, but 'any[]' works for now as we just need status/filename
}

export const api = {
    // === Applications ===
    ingestApplication: async (files: File[]) => {
        const formData = new FormData();
        files.forEach((file) => {
            formData.append("files", file);
        });
        const response = await client.post('/applications/ingest', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    getApplications: async () => {
        const response = await client.get('/applications/');
        return response.data;
    },

    getApplication: async (id: string) => {
        const response = await client.get(`/applications/${id}`);
        return response.data;
    },

    // === Claims ===
    // Note: Old implementation assumed baseURL was .../claims. Now we must prefix.
    ingestClaim: async (file: File) => {
        // Deprecated/Legacy support? Or just redirect to Application ingestion?
        // Let's assume we still use it for single file? 
        // Actually, let's map it to the old endpoint if it still existed, OR forward to new app structure.
        // User asked to clean structure. So we should probably force Application usage.
        // But for minimal breakage, let's keep it if backend supports it.
        // But backend ingestion was refactored. `process_document` requires app_id.
        // So `ingestClaim` is BROKEN unless we fix it to create an app wrapper.
        // Let's change api.ingestClaim to use ingestApplication wrapping single file.
        return api.ingestApplication([file]);
    },

    getQueue: async (status: string = "NEEDS_REVIEW") => {
        const response = await client.get('/claims/queue', { params: { status } });
        return response.data;
    },

    getClaimDetails: async (claimId: string) => {
        const response = await client.get(`/claims/${claimId}/details`);
        return response.data;
    },

    resolveClaim: async (claimId: string, payload: ReviewPayload) => {
        const response = await client.post(`/claims/${claimId}/resolve`, payload);
        return response.data;
    },

    triggerAudit: async (claimId: string) => {
        const response = await client.post(`/claims/${claimId}/audit`);
        return response.data;
    },

    rejectClaim: async (claimId: string) => {
        const response = await client.post(`/claims/${claimId}/reject`);
        return response.data;
    },

    deleteClaim: async (claimId: string) => {
        const response = await client.delete(`/claims/${claimId}`);
        return response.data;
    },

    bulkRejectClaims: async (claimIds: string[]) => {
        const response = await client.post('/bulk-reject', { claim_ids: claimIds });
        return response.data;
    },

    bulkDeleteClaims: async (claimIds: string[]) => {
        const response = await client.post('/bulk-delete', { claim_ids: claimIds });
        return response.data;
    },

    // Debug helper
    simulateExtract: async (_claimId: string) => {
        // Not a real API, but maybe useful for dev? 
        // Actually, trigger extract is a POST /extract
        // But in backend it was mocked in E2E.
        // Let's assume user uses the real backend flow.
        return {};
    }
};
