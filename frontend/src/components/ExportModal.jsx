import React from 'react';
import { X, Download, FileJson, FileSpreadsheet, Globe } from 'lucide-react';

export default function ExportModal({ analysisId, onClose }) {
  if (!analysisId) return null;

  const downloadReport = (format) => {
    window.open(`/api/reports/${analysisId}/export?format=${format}`, '_blank');
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: '28px', maxWidth: '550px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Download size={20} color="#60a5fa" />
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0 }}>Export Consistency Report</h2>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>Select your preferred export format</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* JSON Option */}
          <div
            className="glass-panel"
            onClick={() => downloadReport('json')}
            style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FileJson size={28} color="#6366f1" />
              <div>
                <strong style={{ fontSize: '14px', color: '#f8fafc' }}>JSON Full Fidelity Report</strong>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>Complete structured report schema for CI/CD integration</p>
              </div>
            </div>
            <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>Download</button>
          </div>

          {/* CSV Option */}
          <div
            className="glass-panel"
            onClick={() => downloadReport('csv')}
            style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FileSpreadsheet size={28} color="#10b981" />
              <div>
                <strong style={{ fontSize: '14px', color: '#f8fafc' }}>CSV Spreadsheet Summary</strong>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>Tabular finding log for Excel, Google Sheets, or auditing</p>
              </div>
            </div>
            <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>Download</button>
          </div>

          {/* HTML Option */}
          <div
            className="glass-panel"
            onClick={() => downloadReport('html')}
            style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Globe size={28} color="#f59e0b" />
              <div>
                <strong style={{ fontSize: '14px', color: '#f8fafc' }}>Standalone HTML Report</strong>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>Self-contained visual report viewable in any browser</p>
              </div>
            </div>
            <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>Download</button>
          </div>
        </div>
      </div>
    </div>
  );
}
