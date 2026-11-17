import React, { useState, useEffect } from 'react';
import { X, Award, CheckCircle2, TrendingUp, RefreshCw } from 'lucide-react';

export default function EvaluationModal({ onClose }) {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [enableSemantic, setEnableSemantic] = useState(true);

  const fetchEvaluation = async (semantic) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/evaluate?enable_semantic=${semantic}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('Error fetching evaluation:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvaluation(enableSemantic);
  }, [enableSemantic]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: '28px', maxWidth: '850px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(168, 85, 247, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Award size={20} color="#c084fc" />
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0 }}>
                Benchmark Evaluation (Precision, Recall & F1)
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
                Automated evaluation against labeled ground-truth documentation decay scenarios
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Mode Toggle */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0, 0, 0, 0.3)', padding: '12px 16px', borderRadius: 'var(--radius-md)', marginBottom: '20px' }}>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Evaluation Mode:</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className={`btn ${!enableSemantic ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 12px', fontSize: '12px' }}
              onClick={() => setEnableSemantic(false)}
            >
              Rule-Based Only
            </button>
            <button
              className={`btn ${enableSemantic ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 12px', fontSize: '12px' }}
              onClick={() => setEnableSemantic(true)}
            >
              Hybrid Semantic (TF-IDF + Rules)
            </button>
          </div>
        </div>

        {/* Metrics Cards */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 10px' }} />
            <p>Running benchmark analysis...</p>
          </div>
        ) : metrics ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '24px' }}>
              <div className="glass-panel" style={{ padding: '16px', textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Precision</div>
                <div style={{ fontSize: '28px', fontWeight: '800', color: '#10b981', marginTop: '4px' }}>
                  {(metrics.precision * 100).toFixed(1)}%
                </div>
              </div>
              <div className="glass-panel" style={{ padding: '16px', textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Recall</div>
                <div style={{ fontSize: '28px', fontWeight: '800', color: '#6366f1', marginTop: '4px' }}>
                  {(metrics.recall * 100).toFixed(1)}%
                </div>
              </div>
              <div className="glass-panel" style={{ padding: '16px', textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>F1-Score</div>
                <div style={{ fontSize: '28px', fontWeight: '800', color: '#ec4899', marginTop: '4px' }}>
                  {(metrics.f1_score * 100).toFixed(1)}%
                </div>
              </div>
              <div className="glass-panel" style={{ padding: '16px', textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Total Cases</div>
                <div style={{ fontSize: '28px', fontWeight: '800', color: '#e2e8f0', marginTop: '4px' }}>
                  {metrics.total_evaluated_cases}
                </div>
              </div>
            </div>

            {/* Test Case Confusion Breakdown */}
            <h4 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '10px' }}>
              Benchmark Ground-Truth Confusion Breakdown
            </h4>

            <div style={{ overflowX: 'auto', background: 'rgba(0,0,0,0.3)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '12px' }}>
                    <th style={{ padding: '10px 14px' }}>Case ID</th>
                    <th style={{ padding: '10px 14px' }}>Test Description</th>
                    <th style={{ padding: '10px 14px' }}>Expected</th>
                    <th style={{ padding: '10px 14px' }}>Actual Detected</th>
                    <th style={{ padding: '10px 14px' }}>Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.case_breakdown?.map((c, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', fontWeight: '600', color: '#93c5fd' }}>{c.case_id}</td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>{c.description}</td>
                      <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{c.expected}</td>
                      <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', color: c.actual === c.expected ? '#34d399' : '#fb7185' }}>{c.actual}</td>
                      <td style={{ padding: '10px 14px' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '700',
                          fontFamily: 'var(--font-mono)',
                          background: c.status.startsWith('TRUE') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                          color: c.status.startsWith('TRUE') ? '#34d399' : '#fb7185'
                        }}>
                          {c.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
