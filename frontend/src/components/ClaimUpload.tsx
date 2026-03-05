import React, { useState, useCallback } from "react";
import { api } from "../services/api";
import { useNavigate } from "react-router-dom";

export const ClaimUpload: React.FC = () => {
    const [isDragging, setIsDragging] = useState(false);
    const [status, setStatus] = useState<"IDLE" | "UPLOADING" | "SUCCESS" | "ERROR">("IDLE");
    const [message, setMessage] = useState("");

    const navigate = useNavigate();

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const processFiles = async (files: File[]) => {
        const validFiles: File[] = [];

        for (const file of files) {
            if (file.size > 10 * 1024 * 1024) {
                setStatus("ERROR");
                setMessage(`File ${file.name} too large. Max 10MB.`);
                return;
            }
            if (!["application/pdf", "image/png", "image/jpeg"].includes(file.type)) {
                setStatus("ERROR");
                setMessage(`File ${file.name} invalid type. PDF, PNG, JPG only.`);
                return;
            }
            validFiles.push(file);
        }

        if (validFiles.length === 0) return;

        setStatus("UPLOADING");
        setMessage(`Uploading ${validFiles.length} file(s)...`);

        try {
            const result = await api.ingestApplication(validFiles);
            setStatus("SUCCESS");
            setMessage(`Success! Application ID: ${result.id}`);
            setTimeout(() => {
                navigate("/dashboard");
            }, 1000);
        } catch (err: any) {
            setStatus("ERROR");
            setMessage(err.message || "Upload failed.");
        }
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            processFiles(Array.from(e.dataTransfer.files));
        }
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            processFiles(Array.from(e.target.files));
        }
    };

    return (
        <div className="p-6 max-w-xl mx-auto">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">New Claim Ingestion</h2>

            <div
                className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400"
                    }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <input
                    type="file"
                    id="claim-upload"
                    className="hidden"
                    multiple
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={handleChange}
                />
                <label htmlFor="claim-upload" className="cursor-pointer">
                    <div className="flex flex-col items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <span className="text-gray-600 font-medium">Click to upload or drag and drop</span>
                        <span className="text-sm text-gray-400">PDF, PNG, JPG (max 10MB)</span>
                    </div>
                </label>
            </div>

            {status === "UPLOADING" && (
                <div className="mt-4 p-4 bg-blue-100 text-blue-800 rounded-md flex items-center gap-2">
                    <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                    {message}
                </div>
            )}

            {status === "SUCCESS" && (
                <div className="mt-4 p-4 bg-green-100 text-green-800 rounded-md">
                    ✅ {message}
                </div>
            )}

            {status === "ERROR" && (
                <div className="mt-4 p-4 bg-red-100 text-red-800 rounded-md">
                    ❌ {message}
                </div>
            )}
        </div>
    );
};
