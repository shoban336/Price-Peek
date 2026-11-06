import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Globe, Shield, RefreshCw } from 'lucide-react';
import { getPlatforms, updatePlatform, validateDiscovery } from '../services/api';

export default function AdminRegistryModal({ onClose }) {
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testDomain, setTestDomain] = useState('');
  const [discoveryResult, setDiscoveryResult] = useState(null);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    loadAllPlatforms();
  }, []);

  const loadAllPlatforms = async () => {
    setLoading(true);
    try {
      const data = await getPlatforms(null, false);
      setPlatforms(data.platforms || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (platform) => {
    const newEnabled = !platform.enabled;
    try {
      await updatePlatform(platform.id, { enabled: newEnabled });
      setPlatforms((prev) =>
        prev.map((p) => (p.id === platform.id ? { ...p, enabled: newEnabled } : p))
      );
    } catch (e) {
      alert('Failed to update platform: ' + e.message);
    }
  };

  const handleValidate = async (e) => {
    e.preventDefault();
    if (!testDomain.trim()) return;
    setValidating(true);
    setDiscoveryResult(null);
    try {
      const res = await validateDiscovery(testDomain.trim());
      setDiscoveryResult(res);
    } catch (err) {
      alert('Validation error: ' + err.message);
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>Dynamic Platform Registry & Discovery</h2>
            <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
              Manage active shopping platform connectors and test prospective storefront discovery.
            </p>
          </div>
          <button className="btn-close-modal" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Discovery Validator Tool */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem', marginBottom: '1.5rem' }}>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.4rem', color: '#1e293b' }}>
            Storefront Discovery & robots.txt Compliance Validator
          </h4>
          <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '0.75rem' }}>
            Test prospective shopping platforms against robots.txt directives and server availability.
          </p>
          <form onSubmit={handleValidate} style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              value={testDomain}
              onChange={(e) => setTestDomain(e.target.value)}
              placeholder="e.g. nykaa.com or myntra.com"
              style={{ flex: 1, padding: '0.5rem 0.85rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.88rem' }}
            />
            <button
              type="submit"
              className="btn-search"
              style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
              disabled={validating || !testDomain.trim()}
            >
              {validating ? 'Probing...' : 'Validate'}
            </button>
          </form>

          {discoveryResult && (
            <div style={{ marginTop: '0.85rem', background: 'white', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.75rem', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <strong>Target: {discoveryResult.target}</strong>
                <span
                  style={{
                    fontWeight: 700,
                    color: discoveryResult.recommendation === 'COMPLIANT_CANDIDATE' ? '#16a34a' : '#d97706',
                  }}
                >
                  {discoveryResult.recommendation}
                </span>
              </div>
              <div style={{ color: '#64748b', fontSize: '0.8rem' }}>Robots URL: {discoveryResult.robots_url}</div>
              <div style={{ marginTop: '0.3rem', color: '#334155' }}>{discoveryResult.notes}</div>
            </div>
          )}
        </div>

        {/* Registered Platform Table */}
        <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem', color: '#1e293b' }}>
          Registered Connectors ({platforms.length})
        </h4>

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <div className="spinner" />
          </div>
        ) : (
          <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                <tr>
                  <th style={{ padding: '0.65rem 0.85rem', textAlign: 'left' }}>Platform</th>
                  <th style={{ padding: '0.65rem 0.85rem', textAlign: 'left' }}>Category</th>
                  <th style={{ padding: '0.65rem 0.85rem', textAlign: 'left' }}>Status</th>
                  <th style={{ padding: '0.65rem 0.85rem', textAlign: 'center' }}>Active</th>
                </tr>
              </thead>
              <tbody>
                {platforms.map((p) => (
                  <tr key={p.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.65rem 0.85rem' }}>
                      <strong style={{ display: 'block' }}>{p.name}</strong>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{p.domain}</span>
                    </td>
                    <td style={{ padding: '0.65rem 0.85rem' }}>
                      <span
                        style={{
                          background: '#f1f5f9',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                        }}
                      >
                        {p.category.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ padding: '0.65rem 0.85rem' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          color: p.status === 'AVAILABLE' ? '#16a34a' : '#d97706',
                        }}
                      >
                        {p.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.65rem 0.85rem', textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={p.enabled}
                        onChange={() => handleToggle(p)}
                        style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
