import React from 'react';
import { ExternalLink, Star, Award, Clock, Bell, CheckCircle2 } from 'lucide-react';

const STORE_THEMES = {
  amazon: { bg: '#fff7ed', text: '#ea580c', border: '#fed7aa', name: 'Amazon India' },
  flipkart: { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe', name: 'Flipkart' },
  jiomart: { bg: '#fef2f2', text: '#dc2626', border: '#fecaca', name: 'JioMart' },
  zepto: { bg: '#faf5ff', text: '#7c3aed', border: '#e9d5ff', name: 'Zepto' },
  blinkit: { bg: '#fefce8', text: '#ca8a04', border: '#fef08a', name: 'Blinkit' },
  bigbasket: { bg: '#f0fdf4', text: '#16a34a', border: '#bbf7d0', name: 'BigBasket' },
  myntra: { bg: '#fdf2f8', text: '#db2777', border: '#fbcfe8', name: 'Myntra' },
  ajio: { bg: '#f8fafc', text: '#0f172a', border: '#cbd5e1', name: 'AJIO' },
  croma: { bg: '#ecfeff', text: '#0891b2', border: '#a5f3fc', name: 'Croma' },
  tata1mg: { bg: '#fff1f2', text: '#e11d48', border: '#fecdd3', name: 'Tata 1mg' },
};

export default function PriceComparisonTable({ listings, cheapestId, onOpenAlert }) {
  if (!listings || listings.length === 0) return null;

  return (
    <div className="table-container buyhatke-matrix-container">
      <div className="matrix-header-bar">
        <div>
          <h3 className="matrix-title">Multi-Store Price Comparison Matrix</h3>
          <p className="matrix-subtitle">Real-time side-by-side store prices inspired by Buyhatke</p>
        </div>
        <div className="matrix-legend">
          <span className="legend-chip best"><Award size={13} /> Lowest Price Highlighted</span>
        </div>
      </div>

      <table className="comparison-table buyhatke-table">
        <thead>
          <tr>
            <th>Store</th>
            <th>Product Listing</th>
            <th>Selling Price</th>
            <th>MRP</th>
            <th>Discount</th>
            <th>Delivery Speed</th>
            <th style={{ textAlign: 'right' }}>Direct Store Link</th>
          </tr>
        </thead>
        <tbody>
          {listings.map((item, index) => {
            const isLowest = item.platform_id === cheapestId && item.in_stock !== false;
            const theme = STORE_THEMES[item.platform_id] || { bg: '#f1f5f9', text: '#334155', border: '#e2e8f0' };

            return (
              <tr key={`${item.platform_id}-${index}`} className={isLowest ? 'table-row-cheapest' : ''}>
                <td>
                  <div
                    className="store-matrix-badge"
                    style={{
                      background: theme.bg,
                      color: theme.text,
                      borderColor: theme.border,
                    }}
                  >
                    <span>{item.platform_name}</span>
                  </div>
                  {isLowest && (
                    <span className="best-deal-tag">
                      <Award size={11} /> BEST PRICE
                    </span>
                  )}
                </td>

                <td>
                  <div className="matrix-product-title" title={item.title}>
                    {item.title}
                  </div>
                  {item.rating && (
                    <div className="matrix-rating">
                      <Star size={11} fill="#f59e0b" color="#f59e0b" /> {item.rating} ({item.rating_count || 100}+)
                    </div>
                  )}
                </td>

                <td>
                  <div className="matrix-price-cell">
                    <strong className={`matrix-price ${isLowest ? 'cheapest-green' : ''}`}>
                      ₹{item.price.toLocaleString('en-IN')}
                    </strong>
                    {isLowest && <span className="matrix-savings-hint">Lowest available</span>}
                  </div>
                </td>

                <td>
                  {item.original_price && item.original_price > item.price ? (
                    <span className="matrix-mrp">
                      ₹{item.original_price.toLocaleString('en-IN')}
                    </span>
                  ) : (
                    <span className="matrix-dim">—</span>
                  )}
                </td>

                <td>
                  {item.discount_percent && item.discount_percent > 0 && item.in_stock !== false ? (
                    <span className="matrix-discount-badge">
                      {Math.round(item.discount_percent)}% OFF
                    </span>
                  ) : (
                    <span className="matrix-dim">—</span>
                  )}
                </td>

                <td>
                  <div className={`matrix-delivery ${item.in_stock === false ? 'out-of-stock-txt' : ''}`}>
                    {item.in_stock === false ? (
                      'Out of Stock'
                    ) : (
                      <>
                        <Clock size={13} />
                        <span>{item.delivery_time_estimate || 'Standard'}</span>
                      </>
                    )}
                  </div>
                </td>

                <td style={{ textAlign: 'right' }}>
                  <div className="matrix-action-cell">
                    {onOpenAlert && item.in_stock !== false && (
                      <button
                        className="btn-table-alert"
                        onClick={() => onOpenAlert(item.title, item.price)}
                        title="Set Buyhatke Price Alert"
                      >
                        <Bell size={14} />
                      </button>
                    )}

                    {item.in_stock === false ? (
                      <a
                        href={item.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-view-deal btn-out-of-stock"
                        title={`Check restock status on ${item.platform_name}`}
                      >
                        <span>Out of Stock</span>
                        <ExternalLink size={13} />
                      </a>
                    ) : (
                      <a
                        href={item.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-view-deal btn-buy-store"
                        title={`Buy directly on ${item.platform_name}`}
                      >
                        <span>Buy on Store</span>
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
