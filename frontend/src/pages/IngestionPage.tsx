import React from 'react';
import { ClaimUpload } from '../components/ClaimUpload';

export const IngestionPage: React.FC = () => {
    return (
        <div className="bg-gray-50 min-h-screen py-10">
            <div className="container mx-auto">
                <h1 className="text-3xl font-bold text-center text-gray-800 mb-10">Agentic OCR System</h1>
                <ClaimUpload />
            </div>
        </div>
    );
};
