import React from 'react';
import { ShieldCheck, Database, Award, History, Download, Sparkles } from 'lucide-react';

export default function Header({ 
  backendHealthy, 
  onOpenEvaluation, 
  onOpenHistory, 
  onOpenExport, 
  hasAnalysis 
}) {
  return (
    <header style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      padding: '20px 0',
      marginBottom: '24px',
      borderBottom: '1px solid var(--border-color)',
      flexWrap: 'wrap',
      gap: '16px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '46px',
          height: '46px',
          borderRadius: '12px',
          background: 'var(--accent-gradient)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 16px rgba(99, 102, 241, 0.4)'
        }}>
          <ShieldCheck size={26} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '800', letterSpacing: '-0.02em', margin: 0 }}>
              Knowledge Decay Detector
            </h1>
            <span style={{
              background: 'rgba(99, 102, 241, 0.15)',
              color: '#818cf8',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              padding: '2px 8px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: '700',
              fontFamily: 'var(--font-mono)'
            }}>
              v1.0 LOCAL
            </span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
            Privacy-Preserving Software Documentation Consistency Analyzer
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        {/* Privacy badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          borderRadius: '8px',
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          fontSize: '12px',
          color: '#34d399',
          fontWeight: '500'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: backendHealthy ? '#10b981' : '#f43f5e',
            display: 'inline-block'
          }} />
          {backendHealthy ? '100% Offline • Zero LLM Keys' : 'Connecting to Local Engine...'}
        </div>

        {/* Evaluation Benchmark Button */}
        <button 
          className="btn btn-secondary" 
          onClick={onOpenEvaluation}
          title="Run precision, recall, and F1 evaluation on benchmark test cases"
        >
          <Award size={16} color="#a855f7" />
          <span>Benchmark F1</span>
        </button>

        {/* History Button */}
        <button 
          className="btn btn-secondary" 
          onClick={onOpenHistory}
          title="View past scan results stored in SQLite"
        >
          <History size={16} />
          <span>History</span>
        </button>

        {/* Export Button */}
        {hasAnalysis && (
          <button 
            className="btn btn-secondary" 
            onClick={onOpenExport}
            title="Export Report as JSON, CSV, or HTML"
          >
            <Download size={16} />
            <span>Export</span>
          </button>
        )}
      </div>
    </header>
  );
}
