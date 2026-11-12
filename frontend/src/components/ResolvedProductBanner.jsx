import React from 'react';
import { Link2, ShieldCheck, CheckCircle2, Lock, ExternalLink } from 'lucide-react';

export default function ResolvedProductBanner({ resolvedInfo, parsedQuery, matchingStoreCount }) {
  if (!resolvedInfo?.is_url && !parsedQuery?.is_url_query) {
    return null;
  }

  const title = resolvedInfo?.product_name || resolvedInfo?.clean_query || parsedQuery?.product_name;
  const platformName = resolvedInfo?.platform_name || parsedQuery?.source_platform || 'Pasted URL';
  const tags = resolvedInfo?.locked_variant_tags?.length
    ? resolvedInfo.locked_variant_tags
    : parsedQuery?.locked_variant_tags || [];
  const canonicalUrl = resolvedInfo?.canonical_url;

  return (
    <div className="resolved-product-banner">
      <div className="resolved-header-row">
        <div className="resolved-badge-group">
          <span className="resolved-pill-source">
            <Link2 size={13} />
            <span>Pasted Link: <strong>{platformName}</strong></span>
          </span>
          <span className="resolved-pill-verified">
            <ShieldCheck size={14} color="#16a34a" />
            <span>Exact Variant Locked</span>
          </span>
        </div>

        {matchingStoreCount !== undefined && (
          <div className="resolved-store-count">
            <CheckCircle2 size={15} color="#2563eb" />
            <span><strong>{matchingStoreCount}</strong> {matchingStoreCount === 1 ? 'Store matches' : 'Stores match'} exact specifications</span>
          </div>
        )}
      </div>

      <div className="resolved-body">
        <h2 className="resolved-product-title">
          {title}
        </h2>

        {tags.length > 0 && (
          <div className="locked-variants-wrapper">
            <div className="locked-variants-label">
              <Lock size={13} color="#475569" />
              <span>Locked Variant Attributes:</span>
            </div>
            <div className="locked-tags-container">
              {tags.map((tag, idx) => (
                <span key={idx} className="locked-variant-tag">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="resolved-footer-note">
          <p>
            Zero-Tolerance Match Active: Only stores stocking this <strong>exact</strong> size, weight, color, and technical configuration appear below. Alternative variants and mismatched capacities are strictly excluded.
          </p>
          {canonicalUrl && (
            <a
              href={canonicalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="resolved-source-link"
              title="Open original pasted product page in new tab"
            >
              <span>View Source Product</span>
              <ExternalLink size={12} />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
