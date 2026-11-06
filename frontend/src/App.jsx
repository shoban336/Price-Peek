import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import SearchBar from './components/SearchBar';
import ComparisonSummaryBanner from './components/ComparisonSummaryBanner';
import ProductListingCard from './components/ProductListingCard';
import PriceComparisonTable from './components/PriceComparisonTable';
import PriceHistoryModal from './components/PriceHistoryModal';
import PriceDropAlertModal from './components/PriceDropAlertModal';
import AdminRegistryModal from './components/AdminRegistryModal';
import { searchProducts } from './services/api';
import { LayoutGrid, Table, ArrowUpDown, Filter, AlertCircle, ShoppingBag } from 'lucide-react';
import './styles/App.css';

const CATEGORIES = [
  { id: 'all', label: 'All Stores' },
  { id: 'quick_commerce', label: 'Quick Commerce (10-min)' },
  { id: 'ecommerce', label: 'E-Commerce' },
  { id: 'grocery', label: 'Groceries & Essentials' },
  { id: 'fashion', label: 'Fashion & Apparel' },
  { id: 'electronics', label: 'Electronics & Accessories' },
  { id: 'pharmacy', label: 'Pharmacy' },
  { id: 'beauty', label: 'Beauty & Personal Care' },
];

export default function App() {
  const [pinCode, setPinCode] = useState('560001');
  const [currentQuery, setCurrentQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('cards'); // 'cards' | 'table'
  const [sortBy, setSortBy] = useState('price_asc');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Modals
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [alertTargetProduct, setAlertTargetProduct] = useState({ title: '', price: 0 });

  const handleOpenAlert = (title = null, price = null) => {
    setAlertTargetProduct({
      title: title || searchResults?.parsed_query?.product_name || currentQuery,
      price: price || searchResults?.summary?.lowest_price || 0,
    });
    setShowAlertModal(true);
  };

  // Execute initial search on first render to show immediate value
  useEffect(() => {
    handleSearch('Gold Winner Sunflower Oil 1L');
  }, []);

  const handleSearch = async (queryText) => {
    if (!queryText) return;
    setLoading(true);
    setError(null);
    setCurrentQuery(queryText);

    try {
      const data = await searchProducts(queryText, pinCode, sortBy);
      setSearchResults(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Error communicating with PricePeek backend');
    } finally {
      setLoading(false);
    }
  };

  const handleSortChange = (newSort) => {
    setSortBy(newSort);
    if (currentQuery) {
      handleSearchWithSort(currentQuery, newSort);
    }
  };

  const handleSearchWithSort = async (queryText, sortOption) => {
    setLoading(true);
    try {
      const data = await searchProducts(queryText, pinCode, sortOption);
      setSearchResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Filter listings based on chosen platform category
  const displayedListings = (searchResults?.listings || []).filter((item) => {
    if (selectedCategory === 'all') return true;
    return item.platform_category === selectedCategory;
  });

  const cheapestId = searchResults?.summary?.cheapest_platform_id;

  return (
    <div className="app-container">
      <Navbar
        pinCode={pinCode}
        setPinCode={setPinCode}
        onOpenAdmin={() => setShowAdminModal(true)}
      />

      <SearchBar onSearch={handleSearch} loading={loading} />

      <main className="main-content">
        {error && (
          <div className="state-box" style={{ borderColor: '#fca5a5', background: '#fef2f2' }}>
            <AlertCircle size={32} color="#dc2626" style={{ margin: '0 auto 0.75rem' }} />
            <h3 style={{ color: '#991b1b', marginBottom: '0.4rem' }}>Search Request Error</h3>
            <p style={{ color: '#b91c1c', fontSize: '0.9rem' }}>{error}</p>
          </div>
        )}

        {loading && (
          <div className="state-box">
            <div className="spinner" />
            <h3>Searching Across Platforms...</h3>
            <p style={{ color: '#64748b', fontSize: '0.88rem', marginTop: '0.4rem' }}>
              Querying registered connectors, matching equivalent units & sorting prices...
            </p>
          </div>
        )}

        {!loading && searchResults && (
          <>
            {/* Summary Insights Highlight */}
            <ComparisonSummaryBanner
              summary={searchResults.summary}
              parsedQuery={searchResults.parsed_query}
              onOpenHistory={() => setShowHistoryModal(true)}
              onOpenAlert={() => handleOpenAlert()}
            />

            {/* Category Filter Pills & Controls */}
            <div className="controls-bar">
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.id}
                    className={`suggestion-pill ${selectedCategory === cat.id ? 'active' : ''}`}
                    style={{
                      background: selectedCategory === cat.id ? '#2563eb' : 'white',
                      color: selectedCategory === cat.id ? 'white' : '#334155',
                      borderColor: selectedCategory === cat.id ? '#2563eb' : '#e2e8f0',
                      fontWeight: 600,
                    }}
                    onClick={() => setSelectedCategory(cat.id)}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div className="sort-group">
                  <ArrowUpDown size={15} />
                  <select
                    className="sort-select"
                    value={sortBy}
                    onChange={(e) => handleSortChange(e.target.value)}
                  >
                    <option value="price_asc">Price: Low to High</option>
                    <option value="price_desc">Price: High to Low</option>
                    <option value="discount_desc">Highest Discount</option>
                    <option value="rating_desc">Top Rated</option>
                  </select>
                </div>

                <div className="view-tabs">
                  <button
                    className={`view-tab ${viewMode === 'cards' ? 'active' : ''}`}
                    onClick={() => setViewMode('cards')}
                    title="Grid Card View"
                  >
                    <LayoutGrid size={16} />
                  </button>
                  <button
                    className={`view-tab ${viewMode === 'table' ? 'active' : ''}`}
                    onClick={() => setViewMode('table')}
                    title="Comparative Table View"
                  >
                    <Table size={16} />
                  </button>
                </div>
              </div>
            </div>

            {/* Empty filter result fallback */}
            {displayedListings.length === 0 ? (
              <div className="state-box">
                <ShoppingBag size={36} color="#94a3b8" style={{ margin: '0 auto 0.75rem' }} />
                <h3>No listings in this category</h3>
                <p style={{ color: '#64748b', fontSize: '0.88rem' }}>
                  Try switching back to "All Stores" to view comparison results.
                </p>
              </div>
            ) : viewMode === 'cards' ? (
              <div className="cards-grid">
                {displayedListings.map((item, index) => (
                  <ProductListingCard
                    key={`${item.platform_id}-${index}`}
                    listing={item}
                    isCheapest={item.platform_id === cheapestId}
                  />
                ))}
              </div>
            ) : (
              <PriceComparisonTable
                listings={displayedListings}
                cheapestId={cheapestId}
                onOpenAlert={handleOpenAlert}
              />
            )}
          </>
        )}
      </main>

      {/* Price History Modal */}
      {showHistoryModal && (
        <PriceHistoryModal
          productIdentifier={searchResults?.parsed_query?.raw_query || currentQuery}
          productName={searchResults?.parsed_query?.product_name || currentQuery}
          onClose={() => setShowHistoryModal(false)}
          onOpenAlert={handleOpenAlert}
        />
      )}

      {/* Buyhatke Price Drop Alert Modal */}
      {showAlertModal && (
        <PriceDropAlertModal
          productTitle={alertTargetProduct.title}
          currentPrice={alertTargetProduct.price}
          onClose={() => setShowAlertModal(false)}
        />
      )}

      {/* Admin Platform Registry Modal */}
      {showAdminModal && (
        <AdminRegistryModal onClose={() => setShowAdminModal(false)} />
      )}
    </div>
  );
}
