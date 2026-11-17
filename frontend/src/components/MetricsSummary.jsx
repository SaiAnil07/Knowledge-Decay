import React from 'react';
import { CheckCircle2, AlertOctagon, Clock, HelpCircle, FileText, Compass, AlertTriangle } from 'lucide-react';

export default function MetricsSummary({ summary, onSelectCategory, activeCategory }) {
  if (!summary) return null;

  const totalEvaluated = (summary.consistent || 0) + 
                         (summary.contradictory || 0) + 
                         (summary.potentially_outdated || 0) + 
                         (summary.missing || 0) + 
                         (summary.uncertain || 0);

  // Health score calculation: ratio of consistent items out of all verified checks
  const consistencyScore = totalEvaluated > 0 
    ? Math.round(((summary.consistent || 0) / totalEvaluated) * 100) 
    : 100;

  const cards = [
    {
      key: 'CONSISTENT',
      label: 'Consistent',
      value: summary.consistent || 0,
      icon: CheckCircle2,
      color: 'var(--color-consistent)',
      bg: 'var(--color-consistent-bg)',
      border: 'var(--color-consistent-border)'
    },
    {
      key: 'CONTRADICTORY',
      label: 'Contradictory',
      value: summary.contradictory || 0,
      icon: AlertOctagon,
      color: 'var(--color-contradictory)',
      bg: 'var(--color-contradictory-bg)',
      border: 'var(--color-contradictory-border)'
    },
    {
      key: 'POTENTIALLY_OUTDATED',
      label: 'Outdated / Removed',
      value: summary.potentially_outdated || 0,
      icon: Clock,
      color: 'var(--color-outdated)',
      bg: 'var(--color-outdated-bg)',
      border: 'var(--color-outdated-border)'
    },
    {
      key: 'MISSING',
      label: 'Missing from Docs',
      value: summary.missing || 0,
      icon: Compass,
      color: 'var(--color-missing)',
      bg: 'var(--color-missing-bg)',
      border: 'var(--color-missing-border)'
    },
    {
      key: 'UNCERTAIN',
      label: 'Uncertain Review',
      value: summary.uncertain || 0,
      icon: HelpCircle,
      color: 'var(--color-uncertain)',
      bg: 'var(--color-uncertain-bg)',
      border: 'var(--color-uncertain-border)'
    }
  ];

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '16px'
      }}>
        {/* Health Score Card */}
        <div 
          className="glass-panel" 
          style={{ 
            padding: '20px', 
            position: 'relative', 
            overflow: 'hidden',
            border: '1px solid rgba(99, 102, 241, 0.3)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Documentation Health
            </span>
            <span style={{
              fontSize: '11px',
              padding: '2px 6px',
              borderRadius: '4px',
              background: consistencyScore >= 70 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)',
              color: consistencyScore >= 70 ? '#34d399' : '#fb7185',
              fontWeight: '700'
            }}>
              {consistencyScore >= 70 ? 'STABLE' : 'DECAY DETECTED'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '10px' }}>
            <span style={{ fontSize: '36px', fontWeight: '800', color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
              {consistencyScore}%
            </span>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              ({summary.total_files || 0} files)
            </span>
          </div>

          {/* Progress bar */}
          <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', marginTop: '12px', overflow: 'hidden' }}>
            <div style={{
              width: `${consistencyScore}%`,
              height: '100%',
              background: consistencyScore >= 70 ? 'var(--color-consistent)' : 'var(--color-contradictory)',
              borderRadius: '3px',
              transition: 'width 0.6s ease'
            }} />
          </div>
        </div>

        {/* Dynamic Category Cards */}
        {cards.map((c) => {
          const Icon = c.icon;
          const isActive = activeCategory === c.key;
          return (
            <div
              key={c.key}
              className="glass-panel"
              onClick={() => onSelectCategory(c.key === activeCategory ? 'ALL' : c.key)}
              style={{
                padding: '20px',
                cursor: 'pointer',
                borderColor: isActive ? c.color : 'var(--border-color)',
                boxShadow: isActive ? `0 0 15px ${c.border}` : 'var(--shadow-sm)',
                transform: isActive ? 'translateY(-2px)' : 'none',
                transition: 'all 0.2s ease'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  {c.label}
                </span>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: c.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Icon size={18} color={c.color} />
                </div>
              </div>

              <div style={{ marginTop: '10px', display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                <span style={{ fontSize: '32px', fontWeight: '800', color: c.color, letterSpacing: '-0.02em' }}>
                  {c.value}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  issues
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
