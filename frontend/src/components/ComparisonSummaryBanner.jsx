import React from 'react';
import { Award, TrendingDown, Layers, BarChart2, Bell, ShieldCheck, Sparkles } from 'lucide-react';

export default function ComparisonSummaryBanner({ summary, parsedQuery, onOpenHistory, onOpenAlert }) {
  if (!summary || !summary.lowest_price) return null;

  const currentPrice = summary.lowest_price;
  const avgPrice = summary.average_price || currentPrice;
  const isGoodBuy = currentPrice <= avgPrice;

  return (
    <div className="summary-banner">
      <div className="summary-col-primary">
        <h3>Lowest Available Price</h3>
        <div className="price-highlight">₹{currentPrice.toLocaleString('en-IN')}</div>
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
        <div className="stat-value">₹{avgPrice.toLocaleString('en-IN')}</div>
        <div className="stat-sub">Across {summary.total_active_listings} listings</div>
      </div>

      {/* Buyhatke Decision Actions */}
      <div className="stat-item summary-actions-col">
        <div className="summary-btn-group">
          <button
            className="btn-banner-action"
            onClick={onOpenHistory}
            title="Open Buyhatke Price History & Fluctuations Graph"
          >
            <BarChart2 size={16} />
            <span>Price Graph</span>
          </button>

          {onOpenAlert && (
            <button
              className="btn-banner-action btn-banner-alert"
              onClick={onOpenAlert}
              title="Set Buyhatke Price Drop Alert"
            >
              <Bell size={16} />
              <span>Set Alert</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
