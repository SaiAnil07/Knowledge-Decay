import React, { useState, useEffect } from 'react';
import { X, History, Clock, ArrowRight, Folder } from 'lucide-react';

export default function HistoryModal({ onClose, onLoadRun }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/history')
      .then(r => r.json())
      .then(data => {
        setRuns(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: '28px', maxWidth: '750px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <History size={20} color="#818cf8" />
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0 }}>
                Analysis History (SQLite Local Storage)
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
                Past scans and consistency reports saved locally
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>Loading history...</div>
        ) : runs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>No past runs found in SQLite.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '400px', overflowY: 'auto' }}>
            {runs.map(r => (
              <div
                key={r.id}
                className="glass-panel"
                style={{
                  padding: '14px 18px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer'
                }}
                onClick={() => onLoadRun(r.id)}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <Folder size={14} color="#6366f1" />
                    <strong style={{ fontSize: '13px', color: '#f8fafc' }}>{r.repo_path}</strong>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {new Date(r.timestamp).toLocaleString()} • {r.total_files} files
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span className="badge badge-consistent">{r.consistent}</span>
                    <span className="badge badge-contradictory">{r.contradictory}</span>
                    <span className="badge badge-outdated">{r.outdated}</span>
                    <span className="badge badge-missing">{r.missing}</span>
                  </div>
                  <button className="btn btn-secondary" style={{ padding: '6px 10px', fontSize: '12px' }}>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
