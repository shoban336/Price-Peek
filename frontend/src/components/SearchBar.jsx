import React, { useState, useEffect, useRef } from 'react';
import { Search, Sparkles, X, ArrowUpRight, Loader2 } from 'lucide-react';
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

const FALLBACK_THUMB = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44' viewBox='0 0 24 24' fill='none' stroke='%232563eb' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='m7.5 4.27 9 5.15'/><path d='M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z'/><path d='m3.3 7 8.7 5 8.7-5'/><path d='M12 22V12'/></svg>";

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
        <div className="hero-badge">
          <Sparkles size={14} /> Universal Cross-Store Comparison
        </div>
        <h1 className="hero-title">
          Compare Prices Across <span>All Active Stores</span>
        </h1>
        <p className="hero-subtitle">
          Search groceries, quick commerce, tech, fashion, and medicines.
          Instant PIN-filtered prices with direct product links.
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
              placeholder="Search any product (e.g. Milk, Tomato, Lays, Gold Winner Oil...)"
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
                          src={item.imageUrl || FALLBACK_THUMB}
                          alt={item.name}
                          className="autocomplete-thumb"
                          loading="lazy"
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = FALLBACK_THUMB;
                          }}
                        />
                      </div>

                      <div className="autocomplete-info">
                        <div className="autocomplete-name">{item.name}</div>
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
