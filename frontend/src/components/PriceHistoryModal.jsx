import React, { useEffect, useState } from 'react';
import { X, TrendingDown, TrendingUp, Calendar, RefreshCw, Sparkles, Bell, ShieldCheck, AlertTriangle } from 'lucide-react';
import { getPriceHistory } from '../services/api';

export default function PriceHistoryModal({ productIdentifier, productName, onClose, onOpenAlert }) {
  const [historyData, setHistoryData] = useState([]);
  const [summary, setSummary] = useState(null);
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
      setSummary(data.summary || null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Compute SVG chart coordinates
  const prices = historyData.map((d) => d.price);
  const minPrice = summary?.lowest_price ?? (prices.length ? Math.min(...prices) : 0);
  const maxPrice = summary?.highest_price ?? (prices.length ? Math.max(...prices) : 0);
  const avgPrice = summary?.average_price ?? (prices.length ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : 0);
  const currentPrice = summary?.current_price ?? (prices.length ? prices[prices.length - 1] : 0);
  const priceRange = maxPrice - minPrice || 1;

  const chartWidth = 620;
  const chartHeight = 220;
  const padding = 35;

  const points = historyData.map((item, index) => {
    const x = padding + (index / (Math.max(historyData.length - 1, 1))) * (chartWidth - padding * 2);
    const y = chartHeight - padding - ((item.price - minPrice) / priceRange) * (chartHeight - padding * 2);
    return { x, y, ...item };
  });

  const polylinePoints = points.map((p) => `${p.x},${p.y}`).join(' ');

  // Verdict theme
  const verdict = summary?.verdict;
  const isGoodTime = verdict?.badge === 'good';
  const isWaitTime = verdict?.badge === 'wait';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog buyhatke-history-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge history-icon-badge">
              <TrendingDown size={22} />
            </div>
            <div>
              <h2>Price History & Fluctuations</h2>
              <p className="modal-subtitle">
                Buyhatke Price Tracking Engine · {productName || productIdentifier}
              </p>
            </div>
          </div>
          <button className="btn-close-modal" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Lookback Range Selector */}
        <div className="history-range-bar">
          <div className="history-range-tabs">
            {[7, 15, 30, 90, 180].map((d) => (
              <button
                key={d}
                className={`history-tab ${days === d ? 'active' : ''}`}
                onClick={() => setDays(d)}
              >
                {d} Days
              </button>
            ))}
          </div>

          {onOpenAlert && (
            <button
              className="btn-trigger-alert"
              onClick={() => {
                onClose();
                onOpenAlert(productName, currentPrice);
              }}
            >
              <Bell size={15} /> Set Price Drop Alert
            </button>
          )}
        </div>

        {loading ? (
          <div className="history-loading-box">
            <div className="spinner" />
            <p>Analyzing historical price trends across all stores...</p>
          </div>
        ) : historyData.length === 0 ? (
          <p className="history-empty-text">No price history records recorded yet for this item.</p>
        ) : (
          <div className="history-content-body">
            {/* Buyhatke Decision Verdict Card */}
            {verdict && (
              <div className={`buyhatke-verdict-card ${verdict.badge}`}>
                <div className="verdict-icon-col">
                  {isGoodTime ? (
                    <ShieldCheck size={28} className="verdict-icon good" />
                  ) : isWaitTime ? (
                    <AlertTriangle size={28} className="verdict-icon wait" />
                  ) : (
                    <Sparkles size={28} className="verdict-icon fair" />
                  )}
                </div>
                <div className="verdict-text-col">
                  <div className="verdict-badge-header">
                    <span className="verdict-tag">BUYHATKE PRICE VERDICT</span>
                    <span className="verdict-drop-rate">{verdict.drop_probability}</span>
                  </div>
                  <h3 className="verdict-main-text">{verdict.verdict}</h3>
                  <p className="verdict-reason-text">{verdict.reason}</p>
                </div>
              </div>
            )}

            {/* Stat Cards (Lowest, Highest, Average, Current) */}
            <div className="history-stats-grid">
              <div className="history-stat-card lowest">
                <span className="stat-label">Lowest Recorded</span>
                <span className="stat-val">₹{minPrice.toLocaleString('en-IN')}</span>
                <span className="stat-sub">{summary?.lowest_platform || 'Best Store'}</span>
              </div>

              <div className="history-stat-card highest">
                <span className="stat-label">Highest Recorded</span>
                <span className="stat-val">₹{maxPrice.toLocaleString('en-IN')}</span>
                <span className="stat-sub">{summary?.highest_platform || 'Peak Store'}</span>
              </div>

              <div className="history-stat-card average">
                <span className="stat-label">{days}-Day Average</span>
                <span className="stat-val">₹{avgPrice.toLocaleString('en-IN')}</span>
                <span className="stat-sub">Market Benchmark</span>
              </div>

              <div className="history-stat-card current">
                <span className="stat-label">Current Lowest</span>
                <span className="stat-val highlight">₹{currentPrice.toLocaleString('en-IN')}</span>
                <span className="stat-sub">
                  {summary?.verdict?.savings_vs_peak > 0
                    ? `Save ₹${summary.verdict.savings_vs_peak} vs peak`
                    : 'Active Storefront'}
                </span>
              </div>
            </div>

            {/* Responsive SVG Chart */}
            <div className="chart-wrapper-box">
              <div className="chart-header-row">
                <span className="chart-title">Timeline Price Movement (INR)</span>
                <span className="chart-legend">
                  <span className="legend-dot" /> Multi-Store Trajectory
                </span>
              </div>

              <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="history-svg-chart">
                <defs>
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity="0.22" />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Horizontal reference grid lines */}
                <line x1={padding} y1={padding} x2={chartWidth - padding} y2={padding} stroke="#e2e8f0" strokeDasharray="3 3" />
                <line x1={padding} y1={chartHeight / 2} x2={chartWidth - padding} y2={chartHeight / 2} stroke="#e2e8f0" strokeDasharray="3 3" />
                <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding} stroke="#e2e8f0" strokeDasharray="3 3" />

                {/* Y-axis labels */}
                <text x={padding - 6} y={padding + 4} fontSize="10" textAnchor="end" fill="#94a3b8" fontWeight="600">
                  ₹{maxPrice}
                </text>
                <text x={padding - 6} y={chartHeight / 2 + 4} fontSize="10" textAnchor="end" fill="#94a3b8" fontWeight="600">
                  ₹{avgPrice}
                </text>
                <text x={padding - 6} y={chartHeight - padding + 4} fontSize="10" textAnchor="end" fill="#94a3b8" fontWeight="600">
                  ₹{minPrice}
                </text>

                {/* Filled area */}
                {points.length > 1 && (
                  <polygon
                    fill="url(#chartGradient)"
                    points={`${points[0].x},${chartHeight - padding} ${polylinePoints} ${points[points.length - 1].x},${chartHeight - padding}`}
                  />
                )}

                {/* Polyline */}
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

                {/* Data point markers */}
                {points.map((p, idx) => (
                  <g key={idx} className="chart-point-group">
                    <circle cx={p.x} cy={p.y} r="4.5" fill="#2563eb" stroke="#ffffff" strokeWidth="2" />
                    <text x={p.x} y={p.y - 8} fontSize="9.5" textAnchor="middle" fill="#0f172a" fontWeight="700">
                      ₹{p.price}
                    </text>
                  </g>
                ))}
              </svg>
            </div>

            {/* Observations Table */}
            <div className="observations-box">
              <h4>Store Logged Observations</h4>
              <div className="observations-table-wrap">
                <table className="observations-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Platform</th>
                      <th style={{ textAlign: 'right' }}>Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyData.slice(-10).reverse().map((h, i) => (
                      <tr key={i}>
                        <td className="obs-date">
                          {new Date(h.date).toLocaleDateString()} {new Date(h.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td className="obs-platform">{h.platform_name}</td>
                        <td className="obs-price">₹{h.price.toLocaleString('en-IN')}</td>
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
