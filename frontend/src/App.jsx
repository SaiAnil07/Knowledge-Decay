import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import RepositoryScanner from './components/RepositoryScanner';
import MetricsSummary from './components/MetricsSummary';
import FindingsTable from './components/FindingsTable';
import FindingDetailModal from './components/FindingDetailModal';
import EvaluationModal from './components/EvaluationModal';
import HistoryModal from './components/HistoryModal';
import ExportModal from './components/ExportModal';

export default function App() {
  const [repoPath, setRepoPath] = useState('');
  const [samplePath, setSamplePath] = useState('');
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [enableSemantic, setEnableSemantic] = useState(true);
  const [error, setError] = useState(null);

  const [scanData, setScanData] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [activeCategory, setActiveCategory] = useState('ALL');

  // Modals
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [showEvaluation, setShowEvaluation] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showExport, setShowExport] = useState(false);

  // Check health and fetch sample project path on load
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'healthy') setBackendHealthy(true);
      })
      .catch(() => setBackendHealthy(false));

    fetch('/api/sample-project')
      .then(res => res.json())
      .then(data => {
        if (data.sample_path) {
          setSamplePath(data.sample_path);
          setRepoPath(data.sample_path); // Default to sample project for immediate ease of use
        }
      })
      .catch(err => console.error('Failed to load sample project path:', err));
  }, []);

  const handleScan = async () => {
    if (!repoPath.trim()) return;
    setIsScanning(true);
    setError(null);

    try {
      const res = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_path: repoPath })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Scan failed');
      }

      setScanData(data);
    } catch (err) {
      setError(err.message);
      setScanData(null);
    } finally {
      setIsScanning(false);
    }
  };

  const handleAnalyze = async () => {
    if (!repoPath.trim()) return;
    setIsAnalyzing(true);
    setError(null);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: repoPath,
          enable_semantic: enableSemantic
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Analysis failed');
      }

      setAnalysisData(data);
      // Update scanData with file inventory returned
      setScanData({
        is_valid: true,
        total_files_discovered: data.summary.total_files,
        total_lines: data.summary.total_lines,
        scan_duration_ms: data.summary.scan_duration_ms,
        files: data.files || []
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLoadPastRun = async (analysisId) => {
    try {
      const res = await fetch(`/api/reports/${analysisId}`);
      if (res.ok) {
        const data = await res.json();
        setAnalysisData(data);
        setRepoPath(data.repo_path);
        setShowHistory(false);
      }
    } catch (err) {
      console.error('Error loading past run:', err);
    }
  };

  return (
    <div className="container">
      <Header
        backendHealthy={backendHealthy}
        onOpenEvaluation={() => setShowEvaluation(true)}
        onOpenHistory={() => setShowHistory(true)}
        onOpenExport={() => setShowExport(true)}
        hasAnalysis={!!analysisData}
      />

      <main>
        <RepositoryScanner
          repoPath={repoPath}
          setRepoPath={setRepoPath}
          samplePath={samplePath}
          onScan={handleScan}
          onAnalyze={handleAnalyze}
          isScanning={isScanning}
          isAnalyzing={isAnalyzing}
          scanData={scanData}
          enableSemantic={enableSemantic}
          setEnableSemantic={setEnableSemantic}
          error={error}
        />

        {analysisData && (
          <div className="animate-fade-in">
            <MetricsSummary
              summary={analysisData.summary}
              onSelectCategory={setActiveCategory}
              activeCategory={activeCategory}
            />

            <FindingsTable
              findings={analysisData.findings}
              activeCategory={activeCategory}
              setActiveCategory={setActiveCategory}
              onInspectFinding={setSelectedFinding}
            />
          </div>
        )}
      </main>

      {/* Modals */}
      {selectedFinding && (
        <FindingDetailModal
          finding={selectedFinding}
          onClose={() => setSelectedFinding(null)}
        />
      )}

      {showEvaluation && (
        <EvaluationModal
          onClose={() => setShowEvaluation(false)}
        />
      )}

      {showHistory && (
        <HistoryModal
          onClose={() => setShowHistory(false)}
          onLoadRun={handleLoadPastRun}
        />
      )}

      {showExport && analysisData && (
        <ExportModal
          analysisId={analysisData.analysis_id}
          onClose={() => setShowExport(false)}
        />
      )}
    </div>
  );
}
