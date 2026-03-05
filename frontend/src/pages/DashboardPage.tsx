import React, { useEffect, useState } from 'react';
import { api, ApplicationResponse } from '../services/api';
import { Link } from 'react-router-dom';

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
};

export const DashboardPage: React.FC = () => {
    const [applications, setApplications] = useState<ApplicationResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'PROCESSING' | 'NEEDS_REVIEW' | 'AUDITED' | 'COMPLETED'>('NEEDS_REVIEW');

    useEffect(() => {
        const fetchApps = async () => {
            setLoading(true);
            try {
                // Fetch ALL applications and filter client-side for now
                const data = await api.getApplications();
                setApplications(data);
            } catch (err) {
                console.error("Failed to fetch applications", err);
            } finally {
                setLoading(false);
            }
        };
        fetchApps();
    }, []);

    // Filter displayed apps
    const filteredApps = applications.filter(app => {
        if (activeTab === 'PROCESSING') return app.status === 'PROCESSING' || app.status === 'EXTRACTING';
        return app.status === activeTab;
    });

    return (
        <div className="container mx-auto p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-black">Review Dashboard</h1>
            </div>

            {/* Tabs */}
            <div className="flex space-x-4 mb-4 border-b border-gray-200">
                <button
                    className={`pb-2 px-1 ${activeTab === 'NEEDS_REVIEW' ? 'border-b-2 border-indigo-500 text-indigo-600 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
                    onClick={() => setActiveTab('NEEDS_REVIEW')}
                >
                    Review Queue
                </button>
                <button
                    className={`pb-2 px-1 ${activeTab === 'PROCESSING' ? 'border-b-2 border-indigo-500 text-indigo-600 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
                    onClick={() => setActiveTab('PROCESSING')}
                >
                    Processing
                </button>
                <button
                    className={`pb-2 px-1 ${activeTab === 'AUDITED' ? 'border-b-2 border-indigo-500 text-indigo-600 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
                    onClick={() => setActiveTab('AUDITED')}
                >
                    Audited (2nd Review)
                </button>
                <button
                    className={`pb-2 px-1 ${activeTab === 'COMPLETED' ? 'border-b-2 border-indigo-500 text-indigo-600 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
                    onClick={() => setActiveTab('COMPLETED')}
                >
                    Completed
                </button>
            </div>

            {loading ? (
                <div>Loading...</div>
            ) : (
                <div className="bg-white shadow rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Documents</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {filteredApps.map((app) => (
                                <tr key={app.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-medium">
                                        <div className="flex flex-col">
                                            <span className="text-indigo-600 font-bold">{app.name || 'Application'}</span>
                                            <span className="text-xs text-gray-400 font-mono">{app.id.slice(0, 8)}...</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-gray-500 text-sm">{formatDate(app.created_at)}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                            ${app.status === 'NEEDS_REVIEW' ? 'bg-yellow-100 text-yellow-800' :
                                                app.status === 'AUDITED' ? 'bg-indigo-100 text-indigo-800' :
                                                    app.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800 animate-pulse' :
                                                        'bg-green-100 text-green-800'}`}>
                                            {app.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {/* Nested Document List */}
                                        {app.documents && app.documents.length > 0 ? (
                                            <div className="space-y-1">
                                                {app.documents.map((doc: any) => (
                                                    <div key={doc.id} className="flex items-center justify-between bg-gray-50 px-2 py-1 rounded border border-gray-100">
                                                        <span className="truncate max-w-[150px] font-mono text-xs" title={doc.original_filename}>
                                                            {doc.original_filename}
                                                        </span>
                                                        <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded
                                                            ${doc.status === 'NEEDS_REVIEW' ? 'bg-yellow-200 text-yellow-800' :
                                                                doc.status === 'AUDITED' ? 'bg-indigo-200 text-indigo-800' :
                                                                    doc.status === 'PROCESSING' ? 'bg-blue-200 text-blue-800 animate-pulse' :
                                                                        'bg-green-200 text-green-800'}`}>
                                                            {doc.status}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <span className="text-xs italic text-gray-400">No documents</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                        {app.status === 'PROCESSING' ? (
                                            <span className="text-gray-400 cursor-not-allowed border border-gray-200 px-3 py-1 rounded bg-gray-50">
                                                Processing...
                                            </span>
                                        ) : (
                                            <Link to={`/review/${app.id}`} className="text-indigo-600 hover:text-indigo-900 border border-indigo-200 px-3 py-1 rounded hover:bg-indigo-50">
                                                {activeTab === 'AUDITED' ? 'Finalize' : 'Review App'}
                                            </Link>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {filteredApps.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                                        No applications in this tab.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};
