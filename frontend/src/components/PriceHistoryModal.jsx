import React, { useEffect, useState } from 'react';
import { X, TrendingDown, Calendar, RefreshCw } from 'lucide-react';
import { getPriceHistory } from '../services/api';

export default function PriceHistoryModal({ productIdentifier, productName, onClose }) {
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (productIdentifier) {
      loadHistory(productIdentifier, days);
    }
  }, [productIdentifier, days]);

  const loadHistory = async (id, lookbackDays) => {
    setLoading(true);
    try {
      const data = await getPriceHistory(id, lookbackDays);
      setHistoryData(data.history || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Compute SVG chart coordinates
  const prices = historyData.map((d) => d.price);
  const minPrice = prices.length ? Math.min(...prices) : 0;
  const maxPrice = prices.length ? Math.max(...prices) : 0;
  const priceRange = maxPrice - minPrice || 1;

  const chartWidth = 500;
  const chartHeight = 180;
  const padding = 25;

  const points = historyData.map((item, index) => {
    const x = padding + (index / (Math.max(historyData.length - 1, 1))) * (chartWidth - padding * 2);
    const y = chartHeight - padding - ((item.price - minPrice) / priceRange) * (chartHeight - padding * 2);
    return { x, y, ...item };
  });

  const polylinePoints = points.map((p) => `${p.x},${p.y}`).join(' ');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>Price Movement & Historical Trends</h2>
            <p style={{ fontSize: '0.88rem', color: '#64748b', marginTop: '0.2rem' }}>
              {productName || 'Tracked Product'}
            </p>
          </div>
          <button className="btn-close-modal" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
          {[7, 15, 30, 90].map((d) => (
            <button
              key={d}
              className={`view-tab ${days === d ? 'active' : ''}`}
              onClick={() => setDays(d)}
            >
              {d} Days
            </button>
          ))}
        </div>

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <div className="spinner" />
            <p style={{ color: '#64748b' }}>Loading price timeline...</p>
          </div>
        ) : historyData.length === 0 ? (
          <p style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
            No price history records recorded yet for this item.
          </p>
        ) : (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
              <span style={{ color: '#16a34a', fontWeight: 700 }}>Lowest: ₹{minPrice}</span>
              <span style={{ color: '#dc2626', fontWeight: 700 }}>Highest: ₹{maxPrice}</span>
            </div>

            {/* Responsive SVG Chart */}
            <div style={{ background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1rem', overflowX: 'auto' }}>
              <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
                {/* Horizontal grid lines */}
                <line x1={padding} y1={padding} x2={chartWidth - padding} y2={padding} stroke="#e2e8f0" strokeDasharray="3 3" />
                <line x1={padding} y1={chartHeight / 2} x2={chartWidth - padding} y2={chartHeight / 2} stroke="#e2e8f0" strokeDasharray="3 3" />
                <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding} stroke="#e2e8f0" strokeDasharray="3 3" />

                {/* Line graph */}
                {points.length > 1 && (
                  <polyline
                    fill="none"
                    stroke="#2563eb"
                    strokeWidth="2.5"
                    points={polylinePoints}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Data points */}
                {points.map((p, idx) => (
                  <g key={idx}>
                    <circle cx={p.x} cy={p.y} r="4.5" fill="#2563eb" stroke="#ffffff" strokeWidth="2" />
                    <text x={p.x} y={p.y - 8} fontSize="9" textAnchor="middle" fill="#1e293b" fontWeight="600">
                      ₹{p.price}
                    </text>
                  </g>
                ))}
              </svg>
            </div>

            {/* Recent timeline table */}
            <div style={{ marginTop: '1.25rem' }}>
              <h4 style={{ fontSize: '0.85rem', color: '#475569', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Recorded Observations
              </h4>
              <div style={{ maxHeight: '180px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <tbody>
                    {historyData.map((h, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '0.5rem 0.75rem', color: '#64748b' }}>
                          {new Date(h.date).toLocaleDateString()} {new Date(h.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>{h.platform_name}</td>
                        <td style={{ padding: '0.5rem 0.75rem', fontWeight: 700, color: '#0f172a', textAlign: 'right' }}>
                          ₹{h.price}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
