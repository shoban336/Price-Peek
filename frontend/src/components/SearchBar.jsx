import React, { useState, useEffect, useRef } from 'react';
import { Search, X, ArrowUpRight, Loader2 } from 'lucide-react';
import { fetchAutocompleteSuggestions } from '../services/api';

const POPULAR_SUGGESTIONS = [
  'Gold Winner Sunflower Oil 1L',
  'Amul Taaza Milk 500ml',
  'Fresh Hybrid Tomato',
  'Lay\'s Magic Masala Chips',
  'Dettol Handwash 750ml',
  'Apple iPhone 15 128GB',
  'Dove Intense Repair Shampoo',
  'Dolo 650 tablets strip',
];

/**
 * Category-aware high-fidelity SVG Fallbacks.
 * Ensures that if any external image URL is blocked or fails to load,
 * the item displays an authentic category icon rather than a generic or broken placeholder.
 */
export function getCategoryFallback(category = '', name = '') {
  const combined = `${category} ${name}`.toLowerCase();

  // Dairy (Milk bottle & carton)
  if (combined.includes('dairy') || combined.includes('milk') || combined.includes('dahi') || combined.includes('curd') || combined.includes('butter') || combined.includes('paneer') || combined.includes('cheese')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23e0f2fe' stroke='%230284c7' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><path d='M8 2h8v3H8z'/><path d='M6 5h12v15a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2z'/><path d='M6 11h12'/></svg>";
  }

  // Fruits & Vegetables (Fresh Apple / Tomato)
  if (combined.includes('fruit') || combined.includes('vegetable') || combined.includes('veggie') || combined.includes('tomato') || combined.includes('apple') || combined.includes('potato') || combined.includes('onion') || combined.includes('banana')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23dcfce7' stroke='%2316a34a' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='13' r='8'/><path d='M12 5V2'/><path d='M12 5c2-2 5-2 7 0'/></svg>";
  }

  // Snacks & Munchies (Chips pack)
  if (combined.includes('snack') || combined.includes('chips') || combined.includes('lays') || combined.includes('kurkure') || combined.includes('nachos') || combined.includes('bhujia') || combined.includes('namkeen') || combined.includes('biscuit')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23ffedd5' stroke='%23ea580c' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><path d='M5 4h14l-2 16H7z'/><path d='M9 10h6'/><path d='M9 14h6'/></svg>";
  }

  // Beverages & Cold Drinks
  if (combined.includes('beverage') || combined.includes('drink') || combined.includes('coke') || combined.includes('cola') || combined.includes('juice') || combined.includes('frooti') || combined.includes('coffee') || combined.includes('tea')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23ccfbf1' stroke='%230d9488' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><path d='M17 8h1a4 4 0 1 1 0 8h-1'/><path d='M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z'/><line x1='6' x2='6' y1='2' y2='4'/><line x1='10' x2='10' y1='2' y2='4'/><line x1='14' x2='14' y1='2' y2='4'/></svg>";
  }

  // Edible Oil & Ghee
  if (combined.includes('oil') || combined.includes('sunflower') || combined.includes('ghee') || combined.includes('mustard')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23fef3c7' stroke='%23d97706' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2a5 5 0 0 1 5 5c0 5-5 13-5 13s-5-8-5-13a5 5 0 0 1 5-5Z'/></svg>";
  }

  // Hygiene & Personal Care
  if (combined.includes('personal') || combined.includes('care') || combined.includes('dettol') || combined.includes('handwash') || combined.includes('shampoo') || combined.includes('soap') || combined.includes('toothpaste') || combined.includes('dove')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23e0e7ff' stroke='%234f46e5' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2v4'/><path d='m7 6 10 0'/><rect width='12' height='14' x='6' y='8' rx='2'/><path d='M9 13h6'/></svg>";
  }

  // Tech & Electronics
  if (combined.includes('electronic') || combined.includes('mobile') || combined.includes('phone') || combined.includes('iphone') || combined.includes('case') || combined.includes('headphone') || combined.includes('earbud') || combined.includes('laptop')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23ede9fe' stroke='%237c3aed' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><rect width='14' height='20' x='5' y='2' rx='2'/><path d='M12 18h.01'/></svg>";
  }

  // Fashion & Apparel
  if (combined.includes('fashion') || combined.includes('shirt') || combined.includes('jeans') || combined.includes('pant') || combined.includes('trouser') || combined.includes('shoe') || combined.includes('sneaker') || combined.includes('apparel')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23fae8ff' stroke='%23a855f7' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><path d='M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z'/></svg>";
  }

  // Pharmacy & Health
  if (combined.includes('pharma') || combined.includes('medicine') || combined.includes('tablet') || combined.includes('dolo') || combined.includes('capsule') || combined.includes('strip')) {
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23dcfce7' stroke='%23059669' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><rect width='16' height='16' x='4' y='4' rx='4'/><path d='M12 8v8'/><path d='M8 12h8'/></svg>";
  }

  // General Grocery
  return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='%23f1f5f9' stroke='%23475569' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'><path d='M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z'/><path d='M3 6h18'/><path d='M16 10a4 4 0 0 1-8 0'/></svg>";
}

export default function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isSearchingSuggestions, setIsSearchingSuggestions] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const containerRef = useRef(null);
  const inputRef = useRef(null);

  // Debounced live search autocomplete as user types (300ms)
  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setSuggestions([]);
      setShowDropdown(false);
      setIsSearchingSuggestions(false);
      setActiveIndex(-1);
      return;
    }

    setIsSearchingSuggestions(true);
    const timer = setTimeout(async () => {
      try {
        const results = await fetchAutocompleteSuggestions(trimmed, 8);
        setSuggestions(results);
        setShowDropdown(results && results.length > 0);
        setActiveIndex(-1);
      } catch (err) {
        console.error('Failed to fetch autocomplete:', err);
        setSuggestions([]);
      } finally {
        setIsSearchingSuggestions(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside listener to dismiss suggestion dropdown
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (showDropdown && activeIndex >= 0 && suggestions[activeIndex]) {
      handleSelectItem(suggestions[activeIndex]);
      return;
    }
    if (query.trim()) {
      setShowDropdown(false);
      onSearch(query.trim());
    }
  };

  const handleSelectItem = (item) => {
    const selectedName = item.name || query.trim();
    setQuery(selectedName);
    setShowDropdown(false);
    setActiveIndex(-1);
    onSearch(selectedName);
  };

  const handleSelectPill = (suggestedText) => {
    setQuery(suggestedText);
    setShowDropdown(false);
    onSearch(suggestedText);
  };

  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    setShowDropdown(false);
    if (inputRef.current) inputRef.current.focus();
  };

  const handleKeyDown = (e) => {
    if (!showDropdown || suggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
      setActiveIndex(-1);
    }
  };

  return (
    <section className="hero-section">
      <div className="hero-inner">
        <h1 className="hero-title">
          Compare Prices Across <span>All Active Stores</span>
        </h1>
        <p className="hero-subtitle">
          Paste any direct product link from Amazon, Flipkart, Blinkit, or search by name.
          Real-time price history graphs, drop alerts, and instant store checkout.
        </p>

        <div className="search-box-container" ref={containerRef}>
          <form className="search-form" onSubmit={handleSubmit}>
            <Search size={22} color="#94a3b8" />
            <input
              ref={inputRef}
              type="text"
              className="search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => {
                if (suggestions.length > 0) setShowDropdown(true);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Search product or paste link (e.g. amazon.in/dp/..., Milk, Gold Winner Oil...)"
              autoComplete="off"
            />

            {isSearchingSuggestions && (
              <div className="search-spinner-wrapper" title="Searching live catalog...">
                <Loader2 size={18} className="search-spinner" />
              </div>
            )}

            {query && !isSearchingSuggestions && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={handleClear}
                aria-label="Clear query"
              >
                <X size={16} />
              </button>
            )}

            <button type="submit" className="btn-search" disabled={loading || !query.trim()}>
              {loading ? 'Comparing...' : 'Compare'}
            </button>
          </form>

          {/* Blinkit-style Rich Live Autocomplete Dropdown */}
          {showDropdown && suggestions.length > 0 && (
            <div className="autocomplete-dropdown">
              <div className="autocomplete-header">
                <span className="autocomplete-header-label">Matching Products</span>
                <span className="autocomplete-header-badge">Instant Storefront Lookup</span>
              </div>
              <div className="autocomplete-list" role="listbox">
                {suggestions.map((item, index) => {
                  const isActive = index === activeIndex;
                  const itemTitle = item.title || item.name;
                  const primaryImage = item.image_url || item.imageUrl || getCategoryFallback(item.category, itemTitle);

                  return (
                    <div
                      key={item.id || index}
                      className={`autocomplete-item ${isActive ? 'active' : ''}`}
                      role="option"
                      aria-selected={isActive}
                      onClick={() => handleSelectItem(item)}
                      onMouseEnter={() => setActiveIndex(index)}
                    >
                      <div className="autocomplete-thumb-box">
                        <img
                          src={primaryImage}
                          alt={itemTitle}
                          className="autocomplete-thumb"
                          loading="lazy"
                          onError={(e) => {
                            e.currentTarget.onerror = null;
                            e.currentTarget.src = getCategoryFallback(item.category, itemTitle);
                          }}
                        />
                      </div>

                      <div className="autocomplete-info">
                        <div className="autocomplete-name">{itemTitle}</div>
                        <div className="autocomplete-meta">
                          {item.pack_size && (
                            <span className="autocomplete-pack">{item.pack_size}</span>
                          )}
                          {item.category && (
                            <span className="autocomplete-cat">{item.category}</span>
                          )}
                          {item.subtitle && !item.pack_size && (
                            <span className="autocomplete-subtitle">{item.subtitle}</span>
                          )}
                        </div>
                      </div>

                      <div className="autocomplete-action">
                        <ArrowUpRight size={17} />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="autocomplete-footer">
                <div className="autocomplete-footer-hint">
                  Navigate with <kbd>↑</kbd> <kbd>↓</kbd> and select with <kbd>Enter</kbd>
                </div>
                <div className="autocomplete-footer-count">
                  {suggestions.length} suggestions
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="search-suggestions">
          <span className="suggestion-label">Popular:</span>
          {POPULAR_SUGGESTIONS.map((item) => (
            <button
              key={item}
              className="suggestion-pill"
              onClick={() => handleSelectPill(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
