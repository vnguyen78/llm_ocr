import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { IngestionPage } from './pages/IngestionPage';
import { DashboardPage } from './pages/DashboardPage';
import { ReviewView } from './components/ReviewView';

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-gray-50 flex flex-col">
                <nav className="bg-white shadow p-4">
                    <div className="container mx-auto flex gap-6">
                        <Link to="/" className="font-bold text-blue-600">Ingest</Link>
                        <Link to="/dashboard" className="font-bold text-gray-700 hover:text-blue-600">Dashboard</Link>
                    </div>
                </nav>
                <div className="flex-grow">
                    <Routes>
                        <Route path="/" element={<IngestionPage />} />
                        <Route path="/dashboard" element={<DashboardPage />} />
                        <Route path="/review/:id" element={<ReviewView />} />
                    </Routes>
                </div>
            </div>
        </Router>
    );
}

export default App;
