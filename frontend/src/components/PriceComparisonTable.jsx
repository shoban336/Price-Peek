import React from 'react';
import { ExternalLink, Star } from 'lucide-react';

export default function PriceComparisonTable({ listings, cheapestId }) {
  if (!listings || listings.length === 0) return null;

  return (
    <div className="table-container">
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Store</th>
            <th>Product Listing</th>
            <th>Price</th>
            <th>MRP</th>
            <th>Discount</th>
            <th>Delivery</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {listings.map((item, index) => {
            const isLowest = item.platform_id === cheapestId;
            return (
              <tr key={`${item.platform_id}-${index}`} className={isLowest ? 'table-row-cheapest' : ''}>
                <td>
                  <strong style={{ color: isLowest ? '#15803d' : '#0f172a' }}>
                    {item.platform_name}
                  </strong>
                  {isLowest && (
                    <span
                      style={{
                        display: 'block',
                        fontSize: '0.72rem',
                        color: '#16a34a',
                        fontWeight: 700,
                      }}
                    >
                      BEST DEAL
                    </span>
                  )}
                </td>
                <td>
                  <div style={{ maxWidth: '320px', fontWeight: 500 }}>{item.title}</div>
                </td>
                <td>
                  <strong style={{ fontSize: '1.1rem', color: isLowest ? '#16a34a' : '#0f172a' }}>
                    ₹{item.price.toLocaleString('en-IN')}
                  </strong>
                </td>
                <td>
                  {item.original_price ? (
                    <span style={{ textDecoration: 'line-through', color: '#94a3b8' }}>
                      ₹{item.original_price.toLocaleString('en-IN')}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
                <td>
                  {item.discount_percent ? (
                    <span style={{ color: '#15803d', fontWeight: 700 }}>
                      {Math.round(item.discount_percent)}% off
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
                <td style={{ color: '#475569', fontSize: '0.85rem' }}>
                  {item.delivery_time_estimate || 'Standard'}
                </td>
                <td>
                  <a
                    href={item.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-view-deal"
                    style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', display: 'inline-flex' }}
                    title={`Open exact product page on ${item.platform_name} to Add to Cart`}
                  >
                    <span>View & Buy</span>
                    <ExternalLink size={13} />
                  </a>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
