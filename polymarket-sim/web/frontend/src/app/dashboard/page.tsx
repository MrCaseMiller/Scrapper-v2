/**
 * Dashboard page
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { portfolioAPI } from '../../utils/api';
import TradingControls from '../../components/TradingControls';
import MarketsBrowser from '../../components/MarketsBrowser';

interface Portfolio {
  balance: number;
  total_value: number;
  total_pnl: number;
  total_return_pct: number;
  positions_value: number;
  num_positions: number;
  total_fees_paid: number;
}

interface Position {
  token_id: string;
  market_id: string;
  market_side: string;
  shares: number;
  avg_entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

interface Fill {
  fill_id: string;
  market_id: string;
  side: string;
  shares: number;
  price: number;
  size: number;
  timestamp: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [fills, setFills] = useState<Fill[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPositions, setShowPositions] = useState(false);
  const [showFills, setShowFills] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5s

    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [portfolioData, positionsData, fillsData] = await Promise.all([
        portfolioAPI.getPortfolio(),
        portfolioAPI.getPositions(),
        portfolioAPI.getFills(10),
      ]);

      setPortfolio(portfolioData);
      setPositions(positionsData);
      setFills(fillsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-text-medium">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <header className="bg-bg-primary">
        <div className="max-w-7xl mx-auto px-6 py-5 flex justify-between items-center">
          <h1 className="font-human text-h1 text-text-high">
            Polymarket Sim
          </h1>
          <button
            onClick={handleLogout}
            className="touch-target px-4 py-2 rounded-lg font-human text-body text-text-medium"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Portfolio Summary */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Trading Bot Controls */}
        <div className="mb-8">
          <TradingControls />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="p-6">
            <div className="font-human text-label text-text-medium mb-3">Total Value</div>
            <div className="font-machine text-data text-text-high text-3xl">
              ${portfolio?.total_value.toFixed(2)}
            </div>
          </div>

          <div className="p-6">
            <div className="font-human text-label text-text-medium mb-3">Total P&L</div>
            <div className={`font-machine text-data text-3xl ${
              (portfolio?.total_pnl || 0) >= 0 ? 'text-success' : 'text-error'
            }`}>
              {(portfolio?.total_pnl || 0) >= 0 ? '+' : ''}
              ${portfolio?.total_pnl.toFixed(2)}
            </div>
          </div>

          <div className="p-6">
            <div className="font-human text-label text-text-medium mb-3">Return</div>
            <div className={`font-machine text-data text-3xl ${
              (portfolio?.total_return_pct || 0) >= 0 ? 'text-success' : 'text-error'
            }`}>
              {(portfolio?.total_return_pct || 0) >= 0 ? '+' : ''}
              {portfolio?.total_return_pct.toFixed(1)}%
            </div>
          </div>

          <div className="p-6">
            <div className="font-human text-label text-text-medium mb-3">Positions</div>
            <div className="font-machine text-data text-text-high text-3xl">
              {portfolio?.num_positions || 0}
            </div>
          </div>
        </div>

        {/* Positions */}
        <div className="mb-8">
          <button
            onClick={() => setShowPositions(!showPositions)}
            className="touch-target w-full p-6 flex justify-between items-center"
          >
            <div className="flex items-center gap-4">
              <h2 className="font-human text-h2 text-text-high">Positions</h2>
              <span className="font-machine text-caption text-text-medium">
                {positions.length}
              </span>
            </div>
            <span className="font-human text-body text-text-medium">
              {showPositions ? '−' : '+'}
            </span>
          </button>

          {showPositions && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="text-left px-6 py-3 font-human text-label text-text-medium">Market</th>
                    <th className="text-center px-6 py-3 font-human text-label text-text-medium">Side</th>
                    <th className="text-right px-6 py-3 font-human text-label text-text-medium">Shares</th>
                    <th className="text-right px-6 py-3 font-human text-label text-text-medium">Entry</th>
                    <th className="text-right px-6 py-3 font-human text-label text-text-medium">Current</th>
                    <th className="text-right px-6 py-3 font-human text-label text-text-medium">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-12 font-human text-body text-text-medium">
                        No positions
                      </td>
                    </tr>
                  ) : (
                    positions.map((pos) => (
                      <tr key={pos.token_id} className="touch-target">
                        <td className="px-6 py-4 font-machine text-data text-text-high text-sm">
                          {pos.market_id.substring(0, 20)}...
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="px-2 py-1 bg-accent/20 text-accent font-machine text-caption rounded">
                            {pos.market_side}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right font-machine text-data text-text-high">
                          {pos.shares.toFixed(0)}
                        </td>
                        <td className="px-6 py-4 text-right font-machine text-data text-text-high">
                          ${pos.avg_entry_price.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 text-right font-machine text-data text-text-high">
                          ${pos.current_price.toFixed(2)}
                        </td>
                        <td className={`px-6 py-4 text-right font-machine text-data ${
                          pos.unrealized_pnl >= 0 ? 'text-success' : 'text-error'
                        }`}>
                          {pos.unrealized_pnl >= 0 ? '+' : ''}
                          ${pos.unrealized_pnl.toFixed(2)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Fills */}
        <div className="mb-8">
          <button
            onClick={() => setShowFills(!showFills)}
            className="touch-target w-full p-6 flex justify-between items-center"
          >
            <div className="flex items-center gap-4">
              <h2 className="font-human text-h2 text-text-high">Recent Fills</h2>
              <span className="font-machine text-caption text-text-medium">
                {fills.length}
              </span>
            </div>
            <span className="font-human text-body text-text-medium">
              {showFills ? '−' : '+'}
            </span>
          </button>

          {showFills && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="text-left px-6 py-3 font-human text-label text-text-medium">Time</th>
                    <th className="text-center px-6 py-3 font-human text-label text-text-medium">Side</th>
                    <th className="text-right px-6 py-3 font-human text-label text-text-medium">Shares</th>
                    <th className="text-left px-6 py-3 font-human text-label text-text-medium">Market</th>
                    <th className="text-right px-6 py-3 font-human text-label text-text-medium">Price</th>
                    <th className="text-right px-6 py-3 font-human text-label text-text-medium">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {fills.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-12 font-human text-body text-text-medium">
                        No fills yet
                      </td>
                    </tr>
                  ) : (
                    fills.map((fill) => (
                      <tr key={fill.fill_id} className="touch-target">
                        <td className="px-6 py-4 font-machine text-data text-text-high text-sm">
                          {new Date(fill.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className={`px-2 py-1 font-machine text-caption rounded ${
                            fill.side === 'BUY'
                              ? 'bg-success/20 text-success'
                              : 'bg-error/20 text-error'
                          }`}>
                            {fill.side}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right font-machine text-data text-text-high">
                          {fill.shares.toFixed(0)}
                        </td>
                        <td className="px-6 py-4 font-machine text-data text-text-high text-sm">
                          {fill.market_id.substring(0, 15)}...
                        </td>
                        <td className="px-6 py-4 text-right font-machine text-data text-text-high">
                          ${fill.price.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 text-right font-machine text-data text-text-high">
                          {fill.side === 'BUY' ? '-' : '+'}${fill.size.toFixed(2)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Markets Browser */}
        <MarketsBrowser />
      </div>
    </div>
  );
}
