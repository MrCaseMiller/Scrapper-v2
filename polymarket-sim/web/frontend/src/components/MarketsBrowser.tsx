/**
 * Markets browser component
 */

'use client';

import { useState, useEffect } from 'react';
import { marketsAPI } from '../utils/api';

interface Market {
  market_id: string;
  question: string;
  end_date: string;
  yes_token_id: string;
  no_token_id: string;
  active: boolean;
  category: string | null;
}

export default function MarketsBrowser() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [showMarkets, setShowMarkets] = useState(false);
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);

  useEffect(() => {
    loadMarkets();
  }, []);

  const loadMarkets = async () => {
    try {
      const data = await marketsAPI.getMarkets(20);
      setMarkets(data);
    } catch (error) {
      console.error('Failed to load markets:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button
        onClick={() => setShowMarkets(!showMarkets)}
        className="touch-target w-full p-6 flex justify-between items-center"
      >
        <div className="flex items-center gap-4">
          <h2 className="font-human text-h2 text-text-high">Markets</h2>
          <span className="font-machine text-caption text-text-medium">
            {markets.length}
          </span>
        </div>
        <span className="font-human text-body text-text-medium">
          {showMarkets ? '−' : '+'}
        </span>
      </button>

      {showMarkets && (
        <div className="px-6 pb-6">
          {loading ? (
            <div className="text-center py-12 font-human text-body text-text-medium">
              Loading markets...
            </div>
          ) : markets.length === 0 ? (
            <div className="text-center py-12 font-human text-body text-text-medium">
              No markets available
            </div>
          ) : (
            <div className="space-y-2">
              {markets.map((market) => (
                <div
                  key={market.market_id}
                  onClick={() => setSelectedMarket(
                    selectedMarket?.market_id === market.market_id ? null : market
                  )}
                  className="touch-target p-4 cursor-pointer"
                >
                  {/* Market Header */}
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1">
                      <h3 className="font-human text-body text-text-high mb-2">
                        {market.question}
                      </h3>
                      {market.category && (
                        <span className="inline-block px-2 py-1 bg-accent/20 text-accent font-human text-caption">
                          {market.category}
                        </span>
                      )}
                    </div>
                    <span className="font-human text-body text-text-medium">
                      {selectedMarket?.market_id === market.market_id ? '−' : '+'}
                    </span>
                  </div>

                  {/* Market Details - Progressive Disclosure */}
                  {selectedMarket?.market_id === market.market_id && (
                    <div className="mt-4 pt-4 space-y-2">
                      <div className="flex justify-between">
                        <span className="font-human text-label text-text-medium">End Date</span>
                        <span className="font-machine text-data text-text-high">
                          {new Date(market.end_date).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-human text-label text-text-medium">Market ID</span>
                        <span className="font-machine text-caption text-text-medium">
                          {market.market_id.substring(0, 16)}...
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-human text-label text-text-medium">YES Token</span>
                        <span className="font-machine text-caption text-text-medium">
                          {market.yes_token_id.substring(0, 16)}...
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-human text-label text-text-medium">NO Token</span>
                        <span className="font-machine text-caption text-text-medium">
                          {market.no_token_id.substring(0, 16)}...
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
