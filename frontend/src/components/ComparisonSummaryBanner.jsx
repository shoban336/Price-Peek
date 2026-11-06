import React from 'react';
import { Award, TrendingDown, Layers, BarChart2 } from 'lucide-react';

export default function ComparisonSummaryBanner({ summary, parsedQuery, onOpenHistory }) {
  if (!summary || !summary.lowest_price) return null;

  return (
    <div className="summary-banner">
      <div className="summary-col-primary">
        <h3>Lowest Available Price</h3>
        <div className="price-highlight">₹{summary.lowest_price.toLocaleString('en-IN')}</div>
        <div className="summary-badge-lowest">
          <Award size={14} /> Cheapest on {summary.cheapest_platform}
        </div>
      </div>

      <div className="stat-item">
        <h4>Max Potential Savings</h4>
        <div className="stat-value" style={{ color: '#86efac' }}>
          ₹{(summary.max_savings || 0).toLocaleString('en-IN')}
        </div>
        <div className="stat-sub">Compared to highest store</div>
      </div>

      <div className="stat-item">
        <h4>Average Market Price</h4>
        <div className="stat-value">₹{(summary.average_price || 0).toLocaleString('en-IN')}</div>
        <div className="stat-sub">Across {summary.total_active_listings} listings</div>
      </div>

      <div className="stat-item" style={{ textAlign: 'right' }}>
        <button
          className="btn-registry-admin"
          style={{ background: 'rgba(255, 255, 255, 0.15)', color: 'white', border: 'none', marginLeft: 'auto' }}
          onClick={onOpenHistory}
        >
          <BarChart2 size={16} />
          <span>Price History</span>
        </button>
      </div>
    </div>
  );
}
