/**
 * PricePeek API Client Service
 * Communicates with FastAPI backend endpoints.
 */

const BASE_URL = '/api/v1';

export async function searchProducts(query, pinCode = '560001', sortBy = 'price_asc', platforms = null) {
  const params = new URLSearchParams({
    q: query,
    pin_code: pinCode,
    sort_by: sortBy,
  });
  if (platforms && platforms.length > 0) {
    params.append('platforms', platforms.join(','));
  }

  const response = await fetch(`${BASE_URL}/search?${params.toString()}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Search failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchAutocompleteSuggestions(query, limit = 8) {
  if (!query || !query.trim()) return [];
  try {
    const params = new URLSearchParams({
      q: query.trim(),
      limit: limit.toString(),
    });
    const response = await fetch(`${BASE_URL}/search/autocomplete?${params.toString()}`);
    if (!response.ok) return [];
    return await response.json();
  } catch (err) {
    console.error('Error fetching autocomplete suggestions:', err);
    return [];
  }
}

export async function getPlatforms(category = null, enabledOnly = false) {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (enabledOnly) params.append('enabled_only', 'true');

  const response = await fetch(`${BASE_URL}/platforms?${params.toString()}`);
  if (!response.ok) throw new Error('Failed to load platforms');
  return response.json();
}

export async function updatePlatform(platformId, updates) {
  const response = await fetch(`${BASE_URL}/platforms/${platformId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error('Failed to update platform');
  return response.json();
}

export async function validateDiscovery(domainOrUrl) {
  const response = await fetch(`${BASE_URL}/platforms/validate-discovery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain_or_url: domainOrUrl }),
  });
  if (!response.ok) throw new Error('Discovery validation failed');
  return response.json();
}

export async function getPriceHistory(productIdentifier, days = 30) {
  const response = await fetch(`${BASE_URL}/history/${encodeURIComponent(productIdentifier)}?days=${days}`);
  if (!response.ok) throw new Error('Failed to load price history');
  return response.json();
}
