import React, { useState, useMemo } from 'react';
import { Search, Eye, Filter, CheckCircle, AlertTriangle, AlertCircle, HelpCircle, ArrowRight } from 'lucide-react';

export default function FindingsTable({ findings, activeCategory, setActiveCategory, onInspectFinding }) {
  const [searchQuery, setSearchQuery] = useState('');

  const categoryCounts = useMemo(() => {
    const counts = {
      ALL: findings.length,
      CONTRADICTORY: 0,
      POTENTIALLY_OUTDATED: 0,
      MISSING: 0,
      UNCERTAIN: 0,
      CONSISTENT: 0
    };
    findings.forEach(f => {
      if (counts[f.classification] !== undefined) {
        counts[f.classification]++;
      }
    });
    return counts;
  }, [findings]);

  const filteredFindings = useMemo(() => {
    return findings.filter(f => {
      // Category filter
      if (activeCategory !== 'ALL' && f.classification !== activeCategory) {
        return false;
      }
      // Search query filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const haystack = `
          ${f.title} 
          ${f.explanation} 
          ${f.doc_file || ''} 
          ${f.code_file || ''} 
          ${f.doc_claim || ''} 
          ${f.code_evidence || ''}
          ${f.detection_method}
        `.toLowerCase();
        if (!haystack.includes(query)) {
          return false;
        }
      }
      return true;
    });
  }, [findings, activeCategory, searchQuery]);

  const getBadgeClass = (classification) => {
    switch (classification) {
      case 'CONSISTENT': return 'badge-consistent';
      case 'CONTRADICTORY': return 'badge-contradictory';
      case 'POTENTIALLY_OUTDATED': return 'badge-outdated';
      case 'MISSING': return 'badge-missing';
      case 'UNCERTAIN': return 'badge-uncertain';
      default: return 'badge-uncertain';
    }
  };

  const getCertaintyPill = (certainty) => {
    let color = '#94a3b8';
    let label = certainty;

    if (certainty === 'DEFINITIVE_MISMATCH') {
      color = '#f43f5e';
      label = 'Definitive Mismatch';
    } else if (certainty === 'HIGH_PROBABILITY') {
      color = '#f59e0b';
      label = 'High Probability';
    } else if (certainty === 'HUMAN_REVIEW_RECOMMENDED') {
      color = '#a855f7';
      label = 'Review Recommended';
    } else if (certainty === 'VERIFIED_CONSISTENT') {
      color = '#10b981';
      label = 'Verified Match';
    }

    return (
      <span style={{
        fontSize: '11px',
        fontWeight: '600',
        color: color,
        background: 'rgba(255, 255, 255, 0.04)',
        padding: '2px 8px',
        borderRadius: '4px',
        border: `1px solid ${color}40`,
        fontFamily: 'var(--font-mono)'
      }}>
        {label}
      </span>
    );
  };

  const tabs = [
    { key: 'ALL', label: 'All Findings', count: categoryCounts.ALL },
    { key: 'CONTRADICTORY', label: 'Contradictions', count: categoryCounts.CONTRADICTORY },
    { key: 'POTENTIALLY_OUTDATED', label: 'Outdated / Removed', count: categoryCounts.POTENTIALLY_OUTDATED },
    { key: 'MISSING', label: 'Missing Documentation', count: categoryCounts.MISSING },
    { key: 'UNCERTAIN', label: 'Uncertain Review', count: categoryCounts.UNCERTAIN },
    { key: 'CONSISTENT', label: 'Consistent', count: categoryCounts.CONSISTENT }
  ];

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      {/* Controls Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0 }}>
            Detected Findings & Evidence Log
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
            Inspecting {filteredFindings.length} of {findings.length} total verification results
          </p>
        </div>

        {/* Search input */}
        <div style={{ position: 'relative', width: '280px' }}>
          <Search size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Filter by keyword, path, method..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 34px',
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              fontSize: '13px',
              outline: 'none'
            }}
          />
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        overflowX: 'auto',
        borderBottom: '1px solid var(--border-color)',
        paddingBottom: '12px',
        marginBottom: '20px'
      }}>
        {tabs.map((tab) => {
          const isActive = activeCategory === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveCategory(tab.key)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                border: isActive ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
                borderRadius: 'var(--radius-md)',
                color: isActive ? '#a5b4fc' : 'var(--text-secondary)',
                fontSize: '13px',
                fontWeight: isActive ? '600' : '500',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease'
              }}
            >
              <span>{tab.label}</span>
              <span style={{
                background: isActive ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255, 255, 255, 0.06)',
                color: isActive ? '#ffffff' : 'var(--text-muted)',
                padding: '1px 6px',
                borderRadius: '9999px',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)'
              }}>
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Findings List */}
      {filteredFindings.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-muted)' }}>
          <CheckCircle size={36} color="var(--color-consistent)" style={{ marginBottom: '12px', opacity: 0.8 }} />
          <p style={{ fontSize: '15px', fontWeight: '500' }}>No findings match the selected criteria.</p>
          <p style={{ fontSize: '13px' }}>Try switching category tabs or clearing your search filter.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filteredFindings.map((item) => (
            <div
              key={item.id}
              className="glass-panel"
              style={{
                padding: '18px',
                borderLeft: `4px solid ${
                  item.classification === 'CONSISTENT' ? 'var(--color-consistent)' :
                  item.classification === 'CONTRADICTORY' ? 'var(--color-contradictory)' :
                  item.classification === 'POTENTIALLY_OUTDATED' ? 'var(--color-outdated)' :
                  item.classification === 'MISSING' ? 'var(--color-missing)' : 'var(--color-uncertain)'
                }`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ flex: '1', minWidth: '280px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                    <span className={`badge ${getBadgeClass(item.classification)}`}>
                      {item.classification}
                    </span>
                    {getCertaintyPill(item.certainty)}
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      Method: {item.detection_method}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
                    {item.title}
                  </h3>

                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '10px' }}>
                    {item.explanation}
                  </p>

                  {/* File References Pill Bar */}
                  <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', fontSize: '12px' }}>
                    {item.doc_file && (
                      <span style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        📄 Doc: <strong style={{ color: '#cbd5e1' }}>{item.doc_file}</strong> (line {item.doc_line})
                      </span>
                    )}
                    {item.code_file && (
                      <span style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        💻 Code: <strong style={{ color: '#cbd5e1' }}>{item.code_file}</strong> (line {item.code_line})
                      </span>
                    )}
                  </div>
                </div>

                {/* Inspect Button */}
                <button
                  className="btn btn-secondary"
                  onClick={() => onInspectFinding(item)}
                  style={{ fontSize: '13px', padding: '8px 14px', alignSelf: 'center' }}
                >
                  <Eye size={15} />
                  <span>Inspect Evidence</span>
                </button>
              </div>

              {/* Recommended Action Preview */}
              {item.suggested_action && item.classification !== 'CONSISTENT' && (
                <div style={{
                  marginTop: '12px',
                  padding: '10px 14px',
                  background: 'rgba(99, 102, 241, 0.08)',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  color: '#c7d2fe',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <strong style={{ color: '#818cf8', whiteSpace: 'nowrap' }}>Action:</strong>
                  <span>{item.suggested_action}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
