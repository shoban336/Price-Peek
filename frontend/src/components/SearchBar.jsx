import React, { useState } from 'react';
import { Search, Sparkles } from 'lucide-react';

const SUGGESTIONS = [
  'Gold Winner Sunflower Oil 1L',
  'Dettol Handwash 750ml',
  'iPhone 15 Silicon Phone Case',
  'Men Slim Fit Cotton Casual Shirt',
  'Denim Jeans Pants',
  'Apple iPhone 15 128GB',
  'Dove Intense Repair Shampoo 650ml',
  'Dolo 650 tablets strip',
];

export default function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleSelectSuggestion = (suggestedText) => {
    setQuery(suggestedText);
    onSearch(suggestedText);
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

        <form className="search-form" onSubmit={handleSubmit}>
          <Search size={22} color="#94a3b8" />
          <input
            type="text"
            className="search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search any product (e.g. Gold Winner Sunflower Oil 1L, iPhone 15 256GB...)"
          />
          <button type="submit" className="btn-search" disabled={loading || !query.trim()}>
            {loading ? 'Comparing...' : 'Compare'}
          </button>
        </form>

        <div className="search-suggestions">
          <span className="suggestion-label">Popular:</span>
          {SUGGESTIONS.map((item) => (
            <button
              key={item}
              className="suggestion-pill"
              onClick={() => handleSelectSuggestion(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
