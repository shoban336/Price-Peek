import React from 'react';
import { Search, MapPin, Settings } from 'lucide-react';

const METRO_PINS = [
  { city: 'Bengaluru', pin: '560001' },
  { city: 'Mumbai', pin: '400001' },
  { city: 'Delhi NCR', pin: '110001' },
  { city: 'Chennai', pin: '600001' },
  { city: 'Hyderabad', pin: '500001' },
  { city: 'Kolkata', pin: '700001' },
];

export default function Navbar({ pinCode, setPinCode, onOpenAdmin }) {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="logo-wrapper" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="logo-icon">
            <Search size={20} strokeWidth={2.5} />
          </div>
          <span className="logo-text">
            Price<span>Peek</span>
          </span>
        </div>

        <div className="nav-actions">
          {/* PIN Code Delivery Selector */}
          <div className="pin-selector-box" title="Delivery PIN Code for Quick Commerce & Storefronts">
            <MapPin size={16} color="#2563eb" />
            <input
              type="text"
              className="pin-input"
              value={pinCode}
              maxLength={6}
              onChange={(e) => setPinCode(e.target.value.replace(/\D/g, ''))}
              placeholder="PIN"
            />
            <select
              className="pin-preset-select"
              value={pinCode}
              onChange={(e) => setPinCode(e.target.value)}
            >
              <option value="" disabled>Presets</option>
              {METRO_PINS.map((m) => (
                <option key={m.pin} value={m.pin}>
                  {m.city} ({m.pin})
                </option>
              ))}
            </select>
          </div>

          {/* Admin Platform Registry Button */}
          <button className="btn-registry-admin" onClick={onOpenAdmin}>
            <Settings size={16} />
            <span>Platforms</span>
          </button>
        </div>
      </div>
    </header>
  );
}
