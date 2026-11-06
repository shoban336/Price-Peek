import React, { useState } from 'react';
import { X, Bell, CheckCircle2, TrendingDown, Sparkles, Mail, ShieldAlert } from 'lucide-react';
import { createPriceAlert } from '../services/api';

export default function PriceDropAlertModal({ productTitle, currentPrice, onClose }) {
  const defaultTarget = currentPrice ? Math.round(currentPrice * 0.9) : 100;
  const [targetPrice, setTargetPrice] = useState(defaultTarget);
  const [email, setEmail] = useState(() => localStorage.getItem('pricepeek_alert_email') || '');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const presets = [
    { label: '5% Drop', pct: 0.05 },
    { label: '10% Drop', pct: 0.10 },
    { label: '15% Drop', pct: 0.15 },
  ];

  const handlePreset = (pct) => {
    if (currentPrice) {
      setTargetPrice(Math.round(currentPrice * (1 - pct)));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setError('Please provide a valid email address');
      return;
    }
    if (!targetPrice || targetPrice <= 0) {
      setError('Target price must be greater than 0');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      localStorage.setItem('pricepeek_alert_email', email.trim());
      await createPriceAlert({
        product_name: productTitle || 'Tracked Product',
        target_price: parseFloat(targetPrice),
        current_price: parseFloat(currentPrice || targetPrice),
        email: email.trim(),
      });
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to activate price alert');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog price-alert-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge alert-icon-badge">
              <Bell size={20} />
            </div>
            <div>
              <h2>Price Drop Alert</h2>
              <p className="modal-subtitle">Inspired by Buyhatke Price Watchlist</p>
            </div>
          </div>
          <button className="btn-close-modal" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {success ? (
          <div className="alert-success-box">
            <CheckCircle2 size={48} color="#16a34a" />
            <h3>Price Alert Activated!</h3>
            <p>
              We are continuously tracking <strong>{productTitle}</strong> across Amazon, Flipkart, Blinkit, Zepto, and JioMart.
            </p>
            <div className="alert-success-summary">
              <div>Target Price: <strong>₹{targetPrice}</strong></div>
              <div>Notification to: <strong>{email}</strong></div>
            </div>
            <button className="btn-primary-action" onClick={onClose} style={{ marginTop: '1.25rem', width: '100%' }}>
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="alert-form">
            <div className="alert-product-summary">
              <div className="alert-product-title">{productTitle}</div>
              <div className="alert-current-price-row">
                <span>Current Lowest Price:</span>
                <span className="alert-current-price">₹{currentPrice ? currentPrice.toLocaleString('en-IN') : '--'}</span>
              </div>
            </div>

            {error && (
              <div className="alert-error-banner">
                <ShieldAlert size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="form-group">
              <label>Notify me when price drops to:</label>
              <div className="alert-input-group">
                <span className="currency-prefix">₹</span>
                <input
                  type="number"
                  className="alert-price-input"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  min="1"
                  step="1"
                  required
                />
              </div>

              {/* Quick Presets */}
              <div className="alert-presets-row">
                <span className="preset-label">Quick Targets:</span>
                {presets.map((p) => {
                  const calculated = currentPrice ? Math.round(currentPrice * (1 - p.pct)) : 0;
                  return (
                    <button
                      key={p.label}
                      type="button"
                      className="preset-pill"
                      onClick={() => handlePreset(p.pct)}
                    >
                      {p.label} (₹{calculated})
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="form-group">
              <label>Your Email Address:</label>
              <div className="alert-input-group">
                <Mail size={18} color="#94a3b8" style={{ marginLeft: '0.75rem' }} />
                <input
                  type="email"
                  className="alert-email-input"
                  placeholder="Enter your email for price drop alerts"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="alert-footer-actions">
              <button type="button" className="btn-cancel" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn-save-alert" disabled={loading}>
                {loading ? 'Activating...' : 'Set Price Alert'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
