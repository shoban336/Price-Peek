import React from 'react';
import { ExternalLink, Smartphone, Clock, Star, ShoppingCart } from 'lucide-react';

export default function ProductListingCard({ listing, isCheapest }) {
  const {
    platform_name,
    title,
    price,
    original_price,
    discount_percent,
    product_url,
    deep_link_url,
    rating,
    delivery_time_estimate,
    normalized_quantity,
    normalized_unit,
    variant,
    is_live,
  } = listing;

  return (
    <div className={`product-card ${isCheapest ? 'is-cheapest' : ''}`}>
      {isCheapest && <div className="card-top-badge">Lowest Price</div>}

      <div className="card-platform-header">
        <div className="platform-brand-info">
          <span className="platform-name">{platform_name}</span>
        </div>
        {delivery_time_estimate && (
          <span className="delivery-badge">
            <Clock size={12} /> {delivery_time_estimate}
          </span>
        )}
      </div>

      <h3 className="card-product-title" title={title}>
        {title}
      </h3>

      <div className="card-specs-row">
        {normalized_quantity && normalized_unit && (
          <span className="spec-chip">
            {normalized_quantity} {normalized_unit}
          </span>
        )}
        {variant && <span className="spec-chip">{variant}</span>}
        {rating && (
          <span className="spec-chip" style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#b45309' }}>
            <Star size={11} fill="#f59e0b" color="#f59e0b" /> {rating}
          </span>
        )}
        <span
          className="spec-chip"
          style={{
            color: is_live ? '#15803d' : '#475569',
            backgroundColor: is_live ? '#f0fdf4' : '#f1f5f9',
          }}
          title={is_live ? 'Live storefront extraction' : 'Verified reference listing'}
        >
          {is_live ? '● Live' : 'Reference'}
        </span>
      </div>

      <div className="card-price-row">
        <span className="selling-price">₹{price.toLocaleString('en-IN')}</span>
        {original_price && original_price > price && (
          <span className="original-price">₹{original_price.toLocaleString('en-IN')}</span>
        )}
        {discount_percent && discount_percent > 0 && (
          <span className="discount-chip">-{Math.round(discount_percent)}%</span>
        )}
      </div>

      <div className="card-actions">
        <a
          href={product_url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-view-deal"
          title={`Open exact product page on ${platform_name} to Add to Cart`}
        >
          <ShoppingCart size={15} />
          <span>Add to Cart / View</span>
          <ExternalLink size={13} style={{ opacity: 0.8 }} />
        </a>

        {deep_link_url && (
          <a
            href={deep_link_url}
            className="btn-deep-link"
            title="Open in native mobile app"
          >
            <Smartphone size={16} />
          </a>
        )}
      </div>
    </div>
  );
}
