import React, { useState } from 'react';
import { FolderGit2, Search, Play, FileCode, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';

export default function RepositoryScanner({
  repoPath,
  setRepoPath,
  samplePath,
  onScan,
  onAnalyze,
  isScanning,
  isAnalyzing,
  scanData,
  enableSemantic,
  setEnableSemantic,
  error
}) {
  const [showFileList, setShowFileList] = useState(false);

  const handleUseSample = () => {
    if (samplePath) {
      setRepoPath(samplePath);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <h2 style={{ fontSize: '17px', fontWeight: '700', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FolderGit2 size={20} color="#6366f1" />
            Repository Target
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
            Specify the local folder path containing Java source code, pom.xml, and documentation
          </p>
        </div>

        {samplePath && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleUseSample}
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            <Sparkles size={14} color="#f59e0b" />
            Load Sample Java Project
          </button>
        )}
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <div style={{ flex: '1', minWidth: '300px', position: 'relative' }}>
          <input
            type="text"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="e.g. C:/Users/Username/projects/my-java-service"
            style={{
              width: '100%',
              padding: '12px 16px',
              background: 'rgba(0, 0, 0, 0.35)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-mono)',
              fontSize: '13px',
              outline: 'none',
              transition: 'border-color 0.2s ease'
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--border-focus)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--border-color)')}
          />
        </div>

        <button
          className="btn btn-secondary"
          onClick={onScan}
          disabled={!repoPath.trim() || isScanning || isAnalyzing}
        >
          <Search size={16} />
          {isScanning ? 'Validating...' : 'Scan Files'}
        </button>

        <button
          className="btn btn-primary"
          onClick={onAnalyze}
          disabled={!repoPath.trim() || isScanning || isAnalyzing}
        >
          <Play size={16} />
          {isAnalyzing ? 'Analyzing Consistency...' : 'Run Consistency Analysis'}
        </button>
      </div>

      {/* Semantic NLP Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px', color: 'var(--text-secondary)' }}>
          <input
            type="checkbox"
            checked={enableSemantic}
            onChange={(e) => setEnableSemantic(e.target.checked)}
            style={{ accentColor: '#6366f1', width: '16px', height: '16px', cursor: 'pointer' }}
          />
          <span>Enable Local Semantic NLP Analysis (Scikit-Learn TF-IDF Cosine Similarity)</span>
        </label>

        {scanData && (
          <button
            type="button"
            onClick={() => setShowFileList(!showFileList)}
            style={{ background: 'none', border: 'none', color: '#818cf8', fontSize: '13px', cursor: 'pointer', textDecoration: 'underline' }}
          >
            {showFileList ? 'Hide Discovered Files' : `View ${scanData.total_files_discovered || 0} Discovered Files`}
          </button>
        )}
      </div>

      {/* Error alert */}
      {error && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(244, 63, 94, 0.1)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          borderRadius: 'var(--radius-md)',
          color: '#fb7185',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Scan Quick Summary */}
      {scanData && scanData.is_valid && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Discovered Files:</span>
            <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
              Java: {scanData.counts_by_type?.JAVA || 0}
            </span>
            <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
              Markdown: {scanData.counts_by_type?.MARKDOWN || 0}
            </span>
            <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24' }}>
              README: {scanData.counts_by_type?.README || 0}
            </span>
            <span className="badge" style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc' }}>
              POM: {scanData.counts_by_type?.MAVEN_POM || 0}
            </span>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Scanned in {scanData.scan_duration_ms} ms (Total lines: {scanData.total_lines || 0})
          </span>
        </div>
      )}

      {/* Collapsible file list */}
      {showFileList && scanData?.files && (
        <div style={{
          marginTop: '12px',
          padding: '12px',
          background: 'rgba(0, 0, 0, 0.4)',
          borderRadius: 'var(--radius-md)',
          maxHeight: '180px',
          overflowY: 'auto'
        }}>
          {scanData.files.map((f, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '12px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{f.relative_path}</span>
              <span style={{ color: 'var(--text-muted)' }}>{f.file_type} • {f.line_count} lines</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
