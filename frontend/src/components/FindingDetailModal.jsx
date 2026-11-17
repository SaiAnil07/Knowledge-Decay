import React, { useState } from 'react';
import { X, Copy, Check, FileText, Code2, AlertCircle, Wrench } from 'lucide-react';

export default function FindingDetailModal({ finding, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!finding) return null;

  const handleCopyAction = () => {
    if (finding.suggested_action) {
      navigator.clipboard.writeText(finding.suggested_action);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getBadgeColor = (classification) => {
    switch (classification) {
      case 'CONSISTENT': return 'var(--color-consistent)';
      case 'CONTRADICTORY': return 'var(--color-contradictory)';
      case 'POTENTIALLY_OUTDATED': return 'var(--color-outdated)';
      case 'MISSING': return 'var(--color-missing)';
      default: return 'var(--color-uncertain)';
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: '28px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="badge" style={{
                background: `${getBadgeColor(finding.classification)}20`,
                color: getBadgeColor(finding.classification),
                border: `1px solid ${getBadgeColor(finding.classification)}50`
              }}>
                {finding.classification}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                ID: {finding.id}
              </span>
            </div>
            <h2 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
              {finding.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Detailed Explanation */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
            Analysis Verdict & Rationale
          </h4>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.6', background: 'rgba(255, 255, 255, 0.02)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
            {finding.explanation}
          </p>
        </div>

        {/* Side-by-Side Evidence Comparison */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
          {/* Left: Documentation Claim */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <FileText size={16} color="#38bdf8" />
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#e2e8f0' }}>
                Documentation Artifact
              </span>
            </div>

            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              File: <strong style={{ color: '#cbd5e1' }}>{finding.doc_file || 'None (Missing Documentation)'}</strong>
              {finding.doc_line && <span> (line {finding.doc_line})</span>}
            </div>

            {finding.doc_claim && (
              <div style={{ fontSize: '12px', color: '#93c5fd', marginBottom: '10px', fontFamily: 'var(--font-mono)' }}>
                Claim: {finding.doc_claim}
              </div>
            )}

            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Context Snippet:</div>
            <pre style={{
              background: '#030712',
              padding: '10px',
              borderRadius: '6px',
              fontSize: '12px',
              fontFamily: 'var(--font-mono)',
              color: '#e2e8f0',
              overflowX: 'auto',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              maxHeight: '160px'
            }}>
              {finding.doc_snippet || 'No excerpt available.'}
            </pre>
          </div>

          {/* Right: Code Implementation Evidence */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <Code2 size={16} color="#4ade80" />
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#e2e8f0' }}>
                Implementation Evidence
              </span>
            </div>

            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              File: <strong style={{ color: '#cbd5e1' }}>{finding.code_file || 'None (Removed or Phantom Endpoint)'}</strong>
              {finding.code_line && <span> (line {finding.code_line})</span>}
            </div>

            {finding.code_evidence && (
              <div style={{ fontSize: '12px', color: '#86efac', marginBottom: '10px', fontFamily: 'var(--font-mono)' }}>
                Evidence: {finding.code_evidence}
              </div>
            )}

            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Source AST Context:</div>
            <pre style={{
              background: '#030712',
              padding: '10px',
              borderRadius: '6px',
              fontSize: '12px',
              fontFamily: 'var(--font-mono)',
              color: '#e2e8f0',
              overflowX: 'auto',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              maxHeight: '160px'
            }}>
              {finding.code_snippet || 'No implementation code found.'}
            </pre>
          </div>
        </div>

        {/* Action and Resolution */}
        <div style={{
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          borderRadius: 'var(--radius-md)',
          padding: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <div style={{ flex: '1', minWidth: '260px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#818cf8', fontWeight: '700', fontSize: '12px', marginBottom: '4px' }}>
              <Wrench size={15} />
              RECOMMENDED RESOLUTION
            </div>
            <div style={{ fontSize: '13px', color: '#e0e7ff' }}>
              {finding.suggested_action}
            </div>
          </div>

          <button
            className="btn btn-secondary"
            onClick={handleCopyAction}
            style={{ fontSize: '12px', padding: '8px 14px' }}
          >
            {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
            <span>{copied ? 'Copied to Clipboard!' : 'Copy Fix'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
