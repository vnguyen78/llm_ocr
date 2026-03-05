export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1/claims";

export const ingestClaim = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/ingest`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Upload failed");
    }

    return response.json();
};
