import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, ReviewCorrection, API_URL, ApplicationResponse } from '../services/api';

// --- Document Review Component (Existing Logic) ---
interface DocumentReviewProps {
    claimId: string;
    onBack: () => void;
    onComplete: () => void;
}

const DocumentReview: React.FC<DocumentReviewProps> = ({ claimId, onBack, onComplete }) => {
    const [details, setDetails] = useState<any>(null);
    const [corrections, setCorrections] = useState<ReviewCorrection[]>([]);
    const [loading, setLoading] = useState(true);
    const [focusedValue, setFocusedValue] = useState<string | null>(null);

    // Modal State
    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [approvalNote, setApprovalNote] = useState("");
    const [pendingFlags, setPendingFlags] = useState<any[]>([]);

    useEffect(() => {
        fetchDetails();
    }, [claimId]);

    const fetchDetails = async () => {
        setLoading(true);
        try {
            const data = await api.getClaimDetails(claimId);
            setDetails(data);
            setCorrections([]); // Reset corrections on new load
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleCorrection = (tileId: string, fieldName: string, value: string) => {
        setCorrections(prev => {
            const filtered = prev.filter(c => !(c.tile_id === tileId && c.field_name === fieldName));
            return [...filtered, { tile_id: tileId, field_name: fieldName, new_value: value }];
        });
    };

    const handleSubmit = async (force: boolean = false) => {
        try {
            const payload = {
                corrections,
                confirm_with_issues: force,
                approval_note: force ? approvalNote : undefined
            };

            const result = await api.resolveClaim(claimId, payload);

            if (result.status === 'AUDITED' || result.status === 'COMPLETED') {
                alert("Document Approved & Settled!");
                onComplete();
            } else if (result.remaining_flags && result.remaining_flags.length > 0) {
                setPendingFlags(result.remaining_flags);
                setShowConfirmModal(true);
            } else {
                alert("Review submitted but claim status is: " + result.status);
                fetchDetails();
            }
        } catch (err) {
            console.error(err);
            alert("Failed to submit review.");
        }
    };

    // --- Helper Components ---
    const HighlightedText = ({ text, highlight }: { text: string, highlight: string | null }) => {
        if (!highlight || !text) return <>{text}</>;
        const escaped = highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const flexibleRegex = escaped.replace(/\s+/g, '\\s+');
        const parts = text.split(new RegExp(`(${flexibleRegex})`, 'gi'));
        return (
            <>
                {parts.map((part, i) => {
                    const normPart = part.replace(/\s+/g, ' ').toLowerCase();
                    const normHighlight = highlight.replace(/\s+/g, ' ').toLowerCase();
                    return normPart === normHighlight ?
                        <span key={i} className="bg-yellow-300 text-black font-bold px-1 rounded transition-colors duration-200">{part}</span> :
                        part;
                })}
            </>
        );
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading document details...</div>;
    if (!details) return <div className="p-8 text-center text-red-500">Document details not found</div>;

    return (
        <div className="flex flex-col h-full bg-gray-50">
            {/* Toolbar */}
            <div className="bg-white border-b px-4 py-2 flex justify-between items-center shadow-sm">
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="text-gray-500 hover:text-gray-800 font-medium">
                        &larr; Back to App
                    </button>
                    <h2 className="font-bold text-gray-800">{details.claim.original_filename}</h2>
                    <span className={`px-2 py-0.5 text-xs rounded-full font-bold
                         ${details.claim.status === 'NEEDS_REVIEW' ? 'bg-yellow-100 text-yellow-800' :
                            details.claim.status === 'AUDITED' ? 'bg-indigo-100 text-indigo-800' :
                                'bg-green-100 text-green-800'}`}>
                        {details.claim.status}
                    </span>
                </div>
                <button
                    onClick={() => handleSubmit(false)}
                    className="bg-green-600 text-white px-4 py-1.5 rounded text-sm font-bold hover:bg-green-700 shadow-sm"
                >
                    Resolve Document
                </button>
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* Left Panel: Image Viewer */}
                <div className="w-1/2 bg-gray-900 p-4 overflow-y-auto border-r border-gray-700">
                    <h3 className="text-gray-400 text-xs uppercase font-bold mb-4 tracking-wider">Scanned Images</h3>
                    {details.claim.pages?.length > 0 ? (
                        details.claim.pages.map((page: any) => (
                            <div key={page.id} className="mb-8">
                                {page.tiles?.map((tile: any) => (
                                    <div key={tile.id} className="mb-6 bg-black rounded-lg overflow-hidden border border-gray-700 shadow-lg">
                                        <div className="bg-gray-800 px-3 py-1 text-gray-400 text-xs flex justify-between">
                                            <span>{tile.type}</span>
                                            <span>Tile ID: {tile.id.slice(0, 6)}...</span>
                                        </div>
                                        <div className="relative group">
                                            <img
                                                src={`${API_URL}/${claimId}/tiles/${tile.image_path.split('/').pop()}`}
                                                alt="Tile"
                                                className="w-full h-auto"
                                                onError={(e) => {
                                                    (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x200?text=Image+Not+Found';
                                                }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ))
                    ) : (
                        <div className="text-gray-500 italic">No images found.</div>
                    )}
                </div>

                {/* Right Panel: Data Entry */}
                <div className="w-1/2 bg-white p-6 overflow-y-auto">
                    {/* Compliance/Audit Flags */}
                    {details.flags && details.flags.length > 0 && (
                        <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4">
                            <h3 className="text-red-800 font-bold mb-2">Compliance Issues</h3>
                            <ul className="list-disc ml-5 text-red-700 text-sm">
                                {details.flags.map((f: any, i: number) => (
                                    <li key={i}>{f.description} ({f.code})</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="space-y-8">
                        {details.claim.pages?.map((page: any) =>
                            page.tiles?.map((tile: any) => {
                                const hasExtraction = tile.extraction && tile.extraction.raw_json;
                                const rawFields = hasExtraction ? (tile.extraction.raw_json.fields || {}) : {};
                                const hasTranscription = hasExtraction && !!tile.extraction.raw_json.raw_transcription;

                                let fields: Record<string, any> = {};
                                if (Array.isArray(rawFields)) {
                                    rawFields.forEach((f: any) => { if (f && f.name) fields[f.name] = f; });
                                } else {
                                    fields = rawFields;
                                }

                                const visibleFields = Object.entries(fields).filter(([_, fieldData]: [string, any]) => {
                                    if (typeof fieldData.value === 'object' && fieldData.value !== null) return true;
                                    const val = fieldData.value;
                                    const conf = fieldData.confidence;
                                    const isEmpty = !val || (typeof val === 'string' && val.trim() === '');
                                    if (isEmpty) return false;
                                    if (conf !== undefined && conf >= 1.0) return false;
                                    return true;
                                });

                                return (
                                    <div key={tile.id} className="border-b border-gray-100 pb-6 last:border-0">
                                        <div className="flex justify-between items-end mb-4">
                                            <h4 className="font-bold text-gray-700 text-lg border-b-2 border-blue-500 inline-block pb-1">{tile.type}</h4>
                                            {hasTranscription && (
                                                <span className="text-[10px] uppercase font-bold text-gray-400">Verbatim Text Available</span>
                                            )}
                                        </div>

                                        {!hasExtraction && (
                                            <div className="p-3 bg-red-50 text-red-700 text-sm rounded mb-2">No extraction data.</div>
                                        )}

                                        {hasTranscription && (
                                            <div className="mb-4 p-3 bg-gray-50 border rounded-lg text-sm text-gray-600 leading-relaxed font-serif">
                                                <HighlightedText
                                                    text={tile.extraction.raw_json.raw_transcription}
                                                    highlight={focusedValue}
                                                />
                                            </div>
                                        )}

                                        {hasExtraction && Object.keys(fields).length > 0 && visibleFields.length === 0 && (
                                            <div className="p-3 bg-green-50 text-green-700 text-sm rounded mb-2 flex items-center gap-2">
                                                <span>✓</span> All data confident.
                                            </div>
                                        )}

                                        <div className="space-y-3">
                                            {Object.entries(fields).map(([fieldName, fieldData]: [string, any]) => {
                                                if (typeof fieldData.value === 'object' && fieldData.value !== null) {
                                                    return (
                                                        <div key={fieldName} className="ml-2">
                                                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">{fieldName}</label>
                                                            <textarea
                                                                className="w-full border rounded p-2 text-xs bg-gray-50 font-mono text-black"
                                                                defaultValue={JSON.stringify(fieldData.value, null, 2)}
                                                                rows={4}
                                                                onChange={(e) => {
                                                                    try {
                                                                        const parsed = JSON.parse(e.target.value);
                                                                        handleCorrection(tile.id, fieldName, parsed);
                                                                    } catch (err) { }
                                                                }}
                                                            />
                                                        </div>
                                                    );
                                                }

                                                const val = fieldData.value;
                                                const conf = fieldData.confidence;
                                                const isLowConf = conf !== undefined && conf < 0.9;
                                                const needsReview = fieldData.needs_review === true;
                                                const isEmpty = !val || (typeof val === 'string' && val.trim() === '');

                                                if (isEmpty) return null;
                                                if (conf !== undefined && conf >= 1.0) return null;

                                                return (
                                                    <div key={fieldName} className={`ml-2 p-3 rounded-lg border transition-all ${isLowConf || needsReview ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-200 hover:border-blue-300'}`}>
                                                        <div className="flex justify-between items-center mb-1">
                                                            <label className="text-xs font-bold text-gray-600 uppercase">{fieldName}</label>
                                                            <span className={`text-[10px] font-mono ${isLowConf ? 'text-amber-600 font-bold' : 'text-gray-400'}`}>
                                                                {conf !== undefined ? (Math.round(conf * 100) + '%') : ''}
                                                            </span>
                                                        </div>
                                                        <input
                                                            type="text"
                                                            className="w-full bg-transparent border-b border-gray-300 focus:border-blue-500 focus:outline-none py-1 text-gray-900 font-medium"
                                                            defaultValue={val ?? ''}
                                                            placeholder="N/A"
                                                            onFocus={() => setFocusedValue(val)}
                                                            onBlur={() => setFocusedValue(null)}
                                                            onChange={(e) => handleCorrection(tile.id, fieldName, e.target.value)}
                                                        />
                                                        {(isLowConf || needsReview) && <div className="text-[10px] text-amber-500 mt-1 font-medium">Verify this field</div>}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </div>

            {/* Confirmation Modal */}
            {showConfirmModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg p-6 max-w-lg w-full shadow-xl">
                        <h3 className="text-xl font-bold text-red-600 mb-4">Unresolved Issues</h3>
                        <div className="bg-red-50 p-4 rounded mb-4 border border-red-200 max-h-40 overflow-y-auto">
                            <ul className="list-disc ml-5 text-sm text-red-800">
                                {pendingFlags.map((f: any, i: number) => (
                                    <li key={i}>{f.description}</li>
                                ))}
                            </ul>
                        </div>
                        <p className="mb-2 font-medium text-gray-900">Approve anyway?</p>
                        <textarea
                            className="w-full border rounded p-2 mb-4 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                            rows={3}
                            placeholder="Reason for approval (required)..."
                            value={approvalNote}
                            onChange={(e) => setApprovalNote(e.target.value)}
                        />
                        <div className="flex justify-end gap-3">
                            <button onClick={() => setShowConfirmModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                            <button onClick={() => { if (!approvalNote.trim()) { alert("Note required."); return; } handleSubmit(true); }} className="px-4 py-2 bg-blue-600 text-white font-bold rounded hover:bg-blue-700">Approve with Note</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// --- Main Application Wrapper ---
export const ReviewView: React.FC = () => {
    const { id } = useParams<{ id: string }>(); // This is Application ID now
    const navigate = useNavigate();
    const [application, setApplication] = useState<ApplicationResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        fetchApplication();
    }, [id]);

    const fetchApplication = async () => {
        setLoading(true);
        try {
            const app = await api.getApplication(id!);
            setApplication(app);
            // Select first document if none selected
            if (!selectedClaimId && app.documents && app.documents.length > 0) {
                // Find first non-completed or just first
                const firstTodo = app.documents.find((d: any) => d.status === 'NEEDS_REVIEW') || app.documents[0];
                setSelectedClaimId(firstTodo.id);
            }
        } catch (err) {
            console.error("Failed to fetch application", err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8">Loading Application...</div>;
    if (!application) return <div className="p-8 text-red-600">Application not found</div>;

    // If a document is selected, show DocumentReview
    if (selectedClaimId) {
        return (
            <div className="flex h-screen overflow-hidden bg-gray-100">
                {/* Sidebar - Document List */}
                <div className="w-64 bg-white border-r border-gray-200 flex flex-col shadow-lg z-10">
                    <div className="p-4 border-b">
                        <h2 className="font-bold text-gray-700">Application Docs</h2>
                        <div className="text-xs text-gray-500 mt-1">ID: {application.id.slice(0, 8)}</div>
                        <div className="mt-2 text-xs font-semibold bg-blue-50 text-blue-700 px-2 py-1 rounded inline-block">
                            {application.status}
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-2">
                        {application.documents?.map((doc: any) => (
                            <button
                                key={doc.id}
                                onClick={() => setSelectedClaimId(doc.id)}
                                className={`w-full text-left p-3 rounded-lg text-sm border transition-all
                                    ${selectedClaimId === doc.id
                                        ? 'bg-blue-600 text-white border-blue-600 shadow-md transform scale-[1.02]'
                                        : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300 hover:bg-blue-50'}`}
                            >
                                <div className="font-medium truncate mb-1" title={doc.original_filename}>
                                    {doc.original_filename}
                                </div>
                                <div className="flex justify-between items-center opacity-90">
                                    <span className="text-[10px] uppercase font-bold tracking-wider">{doc.status}</span>
                                    {doc.status === 'AUDITED' && <span>✓</span>}
                                </div>
                            </button>
                        ))}
                    </div>
                    <div className="p-4 border-t bg-gray-50">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="w-full py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded bg-white hover:bg-gray-50"
                        >
                            Exit Review
                        </button>
                    </div>
                </div>

                {/* Main Content - Document Review */}
                <div className="flex-1 relative">
                    <DocumentReview
                        claimId={selectedClaimId}
                        onBack={() => navigate('/dashboard')}
                        onComplete={() => {
                            fetchApplication(); // Refresh status
                        }}
                    />
                </div>
            </div>
        );
    }

    return <div>Select a document to review.</div>;
};
