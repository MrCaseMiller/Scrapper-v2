/**
 * Dashboard page
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { portfolioAPI } from '../../utils/api';

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
      <header className="border-b border-text-low">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-text-high">
            Polymarket Sim
          </h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-text-medium hover:text-text-high transition-colors"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Portfolio Summary */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-bg-secondary p-6 rounded-8 border border-text-low">
            <div className="text-text-medium text-sm mb-2">Total Value</div>
            <div className="text-text-high text-3xl font-mono">
              ${portfolio?.total_value.toFixed(2)}
            </div>
          </div>

          <div className="bg-bg-secondary p-6 rounded-8 border border-text-low">
            <div className="text-text-medium text-sm mb-2">Total P&L</div>
            <div className={`text-3xl font-mono ${
              (portfolio?.total_pnl || 0) >= 0 ? 'text-success' : 'text-error'
            }`}>
              {(portfolio?.total_pnl || 0) >= 0 ? '+' : ''}
              ${portfolio?.total_pnl.toFixed(2)}
            </div>
          </div>

          <div className="bg-bg-secondary p-6 rounded-8 border border-text-low">
            <div className="text-text-medium text-sm mb-2">Return</div>
            <div className={`text-3xl font-mono ${
              (portfolio?.total_return_pct || 0) >= 0 ? 'text-success' : 'text-error'
            }`}>
              {(portfolio?.total_return_pct || 0) >= 0 ? '+' : ''}
              {portfolio?.total_return_pct.toFixed(1)}%
            </div>
          </div>

          <div className="bg-bg-secondary p-6 rounded-8 border border-text-low">
            <div className="text-text-medium text-sm mb-2">Positions</div>
            <div className="text-text-high text-3xl font-mono">
              {portfolio?.num_positions || 0}
            </div>
          </div>
        </div>

        {/* Positions */}
        <div className="bg-bg-secondary rounded-8 border border-text-low mb-8">
          <div className="p-6 border-b border-text-low">
            <h2 className="text-xl font-bold text-text-high">Positions</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-text-low">
                  <th className="text-left p-4 text-text-medium text-sm font-normal">Market</th>
                  <th className="text-center p-4 text-text-medium text-sm font-normal">Side</th>
                  <th className="text-right p-4 text-text-medium text-sm font-normal">Shares</th>
                  <th className="text-right p-4 text-text-medium text-sm font-normal">Entry</th>
                  <th className="text-right p-4 text-text-medium text-sm font-normal">Current</th>
                  <th className="text-right p-4 text-text-medium text-sm font-normal">P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center p-8 text-text-medium">
                      No positions
                    </td>
                  </tr>
                ) : (
                  positions.map((pos) => (
                    <tr key={pos.token_id} className="border-b border-text-low last:border-0">
                      <td className="p-4 text-text-high font-mono text-sm">
                        {pos.market_id.substring(0, 20)}...
                      </td>
                      <td className="p-4 text-center">
                        <span className="px-2 py-1 bg-accent/20 text-accent text-xs font-mono rounded">
                          {pos.market_side}
                        </span>
                      </td>
                      <td className="p-4 text-right text-text-high font-mono">
                        {pos.shares.toFixed(0)}
                      </td>
                      <td className="p-4 text-right text-text-high font-mono">
                        ${pos.avg_entry_price.toFixed(2)}
                      </td>
                      <td className="p-4 text-right text-text-high font-mono">
                        ${pos.current_price.toFixed(2)}
                      </td>
                      <td className={`p-4 text-right font-mono ${
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
        </div>

        {/* Recent Fills */}
        <div className="bg-bg-secondary rounded-8 border border-text-low">
          <div className="p-6 border-b border-text-low">
            <h2 className="text-xl font-bold text-text-high">Recent Fills</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-text-low">
                  <th className="text-left p-4 text-text-medium text-sm font-normal">Time</th>
                  <th className="text-center p-4 text-text-medium text-sm font-normal">Side</th>
                  <th className="text-right p-4 text-text-medium text-sm font-normal">Shares</th>
                  <th className="text-left p-4 text-text-medium text-sm font-normal">Market</th>
                  <th className="text-right p-4 text-text-medium text-sm font-normal">Price</th>
                  <th className="text-right p-4 text-text-medium text-sm font-normal">Cost</th>
                </tr>
              </thead>
              <tbody>
                {fills.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center p-8 text-text-medium">
                      No fills yet
                    </td>
                  </tr>
                ) : (
                  fills.map((fill) => (
                    <tr key={fill.fill_id} className="border-b border-text-low last:border-0">
                      <td className="p-4 text-text-high font-mono text-sm">
                        {new Date(fill.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="p-4 text-center">
                        <span className={`px-2 py-1 text-xs font-mono rounded ${
                          fill.side === 'BUY'
                            ? 'bg-success/20 text-success'
                            : 'bg-error/20 text-error'
                        }`}>
                          {fill.side}
                        </span>
                      </td>
                      <td className="p-4 text-right text-text-high font-mono">
                        {fill.shares.toFixed(0)}
                      </td>
                      <td className="p-4 text-text-high font-mono text-sm">
                        {fill.market_id.substring(0, 15)}...
                      </td>
                      <td className="p-4 text-right text-text-high font-mono">
                        ${fill.price.toFixed(2)}
                      </td>
                      <td className="p-4 text-right text-text-high font-mono">
                        {fill.side === 'BUY' ? '-' : '+'}${fill.size.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
