/**
 * Trading bot controls component with all 7 strategies
 * Last updated: 2026-02-13 19:45 PST - Force rebuild with all strategies
 */

'use client';

import { useState, useEffect } from 'react';
import { botAPI, marketsAPI } from '../utils/api';

interface TradingControlsProps {
  onBotStatusChange?: (status: any) => void;
}

// Strategy metadata type
interface StrategyMetadata {
  name: string;
  description: string;
  risk: string;
  complexity: string;
  icon: string;
  recommended?: boolean;
}

// Strategy metadata
const STRATEGIES: Record<string, StrategyMetadata> = {
  // Original strategies
  threshold: {
    name: 'Threshold',
    description: 'Buy below/sell above price thresholds',
    risk: 'Low',
    complexity: 'Simple',
    icon: '📊'
  },
  mean_reversion: {
    name: 'Mean Reversion',
    description: 'Trade when price deviates from mean',
    risk: 'Medium',
    complexity: 'Medium',
    icon: '📉'
  },
  manual: {
    name: 'Manual',
    description: 'Manual control via API',
    risk: 'Custom',
    complexity: 'Simple',
    icon: '🎮'
  },

  // New professional strategies
  sum_to_one_arb: {
    name: 'Sum-to-One Arb',
    description: 'Arbitrage YES+NO mispricing (2.5%+ spread)',
    risk: 'Very Low',
    complexity: 'Low',
    icon: '🎯',
    recommended: true
  },
  momentum_lag_arb: {
    name: 'Momentum/Lag Arb',
    description: 'Front-run 15-min markets using spot exchange data',
    risk: 'Medium',
    complexity: 'Medium',
    icon: '🚀'
  },
  market_making: {
    name: 'Market Making',
    description: 'Provide liquidity and earn bid-ask spreads',
    risk: 'Medium',
    complexity: 'High',
    icon: '💧'
  },
  llm_directional: {
    name: 'LLM Directional',
    description: 'AI-driven directional betting using news analysis',
    risk: 'High',
    complexity: 'Very High',
    icon: '🤖'
  },
};

export default function TradingControls({ onBotStatusChange }: TradingControlsProps) {
  const [botStatus, setBotStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  // General config
  const [strategy, setStrategy] = useState('sum_to_one_arb'); // Default to safest strategy
  const [maxMarkets, setMaxMarkets] = useState(10);
  const [updateInterval, setUpdateInterval] = useState(5);

  // Threshold strategy params
  const [buyBelow, setBuyBelow] = useState(0.3);
  const [sellAbove, setSellAbove] = useState(0.7);
  const [positionSize, setPositionSize] = useState(100);

  // Sum-to-One Arb params
  const [minSpreadPct, setMinSpreadPct] = useState(2.5);
  const [feeRate, setFeeRate] = useState(0.02);
  const [maxPositionSize, setMaxPositionSize] = useState(500);

  // Momentum/Lag Arb params
  const [momentumThreshold, setMomentumThreshold] = useState(0.4);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.65);
  const [assets, setAssets] = useState('BTC,ETH,SOL');

  // Market Making params
  const [baseSpread, setBaseSpread] = useState(0.02);
  const [orderSize, setOrderSize] = useState(100);
  const [maxInventory, setMaxInventory] = useState(500);

  // LLM Directional params
  const [minEdgePct, setMinEdgePct] = useState(15.0);
  const [llmConfidenceThreshold, setLlmConfidenceThreshold] = useState(0.7);
  const [newsLookbackHours, setNewsLookbackHours] = useState(24);

  useEffect(() => {
    loadBotStatus();
    const interval = setInterval(loadBotStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const loadBotStatus = async () => {
    try {
      const status = await botAPI.getStatus();
      setBotStatus(status);
      if (onBotStatusChange) {
        onBotStatusChange(status);
      }
    } catch (error) {
      setBotStatus(null);
    }
  };

  const getStrategyParams = () => {
    switch (strategy) {
      case 'threshold':
        return {
          buy_below: buyBelow,
          sell_above: sellAbove,
          position_size: positionSize,
        };

      case 'sum_to_one_arb':
        return {
          min_spread_pct: minSpreadPct,
          fee_rate: feeRate,
          max_position_size: maxPositionSize,
        };

      case 'momentum_lag_arb':
        return {
          momentum_threshold: momentumThreshold,
          confidence_threshold: confidenceThreshold,
          assets: assets.split(',').map(a => a.trim()),
          max_position_size: maxPositionSize,
        };

      case 'market_making':
        return {
          base_spread: baseSpread,
          order_size: orderSize,
          max_inventory: maxInventory,
        };

      case 'llm_directional':
        return {
          min_edge_pct: minEdgePct,
          confidence_threshold: llmConfidenceThreshold,
          news_lookback_hours: newsLookbackHours,
          max_position_size: maxPositionSize,
        };

      default:
        return {};
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      const config = {
        strategy,
        max_markets: maxMarkets,
        update_interval: updateInterval,
        strategy_params: getStrategyParams(),
      };

      const status = await botAPI.start(config);
      setBotStatus(status);
      setShowConfig(false);
    } catch (error: any) {
      console.error('Failed to start bot:', error);
      alert('Failed to start bot: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await botAPI.stop();
      setBotStatus(null);
    } catch (error) {
      console.error('Failed to stop bot:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderStrategyConfig = () => {
    switch (strategy) {
      case 'threshold':
        return (
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block font-human text-label text-text-medium mb-2">
                Buy Below
              </label>
              <input
                type="number"
                value={buyBelow}
                onChange={(e) => setBuyBelow(parseFloat(e.target.value))}
                min={0}
                max={1}
                step={0.05}
                className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
              />
            </div>
            <div>
              <label className="block font-human text-label text-text-medium mb-2">
                Sell Above
              </label>
              <input
                type="number"
                value={sellAbove}
                onChange={(e) => setSellAbove(parseFloat(e.target.value))}
                min={0}
                max={1}
                step={0.05}
                className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
              />
            </div>
            <div>
              <label className="block font-human text-label text-text-medium mb-2">
                Position Size ($)
              </label>
              <input
                type="number"
                value={positionSize}
                onChange={(e) => setPositionSize(parseFloat(e.target.value))}
                min={10}
                max={1000}
                step={10}
                className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
              />
            </div>
          </div>
        );

      case 'sum_to_one_arb':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Min Spread (%)
                  <span className="block text-caption text-text-low">Minimum profitable spread</span>
                </label>
                <input
                  type="number"
                  value={minSpreadPct}
                  onChange={(e) => setMinSpreadPct(parseFloat(e.target.value))}
                  min={1.0}
                  max={10.0}
                  step={0.1}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Fee Rate
                  <span className="block text-caption text-text-low">Polymarket fee (2%)</span>
                </label>
                <input
                  type="number"
                  value={feeRate}
                  onChange={(e) => setFeeRate(parseFloat(e.target.value))}
                  min={0}
                  max={0.1}
                  step={0.001}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Max Position ($)
                  <span className="block text-caption text-text-low">Max per arbitrage</span>
                </label>
                <input
                  type="number"
                  value={maxPositionSize}
                  onChange={(e) => setMaxPositionSize(parseFloat(e.target.value))}
                  min={50}
                  max={5000}
                  step={50}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>
          </div>
        );

      case 'momentum_lag_arb':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Momentum Threshold (%)
                  <span className="block text-caption text-text-low">Min price move</span>
                </label>
                <input
                  type="number"
                  value={momentumThreshold}
                  onChange={(e) => setMomentumThreshold(parseFloat(e.target.value))}
                  min={0.1}
                  max={2.0}
                  step={0.1}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Confidence Threshold
                  <span className="block text-caption text-text-low">Min confidence</span>
                </label>
                <input
                  type="number"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  min={0.5}
                  max={1.0}
                  step={0.05}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Assets
                  <span className="block text-caption text-text-low">Comma-separated</span>
                </label>
                <input
                  type="text"
                  value={assets}
                  onChange={(e) => setAssets(e.target.value)}
                  placeholder="BTC,ETH,SOL"
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>
          </div>
        );

      case 'market_making':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Base Spread (%)
                  <span className="block text-caption text-text-low">Bid-ask spread</span>
                </label>
                <input
                  type="number"
                  value={baseSpread}
                  onChange={(e) => setBaseSpread(parseFloat(e.target.value))}
                  min={0.005}
                  max={0.1}
                  step={0.005}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Order Size ($)
                  <span className="block text-caption text-text-low">Per side</span>
                </label>
                <input
                  type="number"
                  value={orderSize}
                  onChange={(e) => setOrderSize(parseFloat(e.target.value))}
                  min={10}
                  max={500}
                  step={10}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Max Inventory ($)
                  <span className="block text-caption text-text-low">Position limit</span>
                </label>
                <input
                  type="number"
                  value={maxInventory}
                  onChange={(e) => setMaxInventory(parseFloat(e.target.value))}
                  min={100}
                  max={5000}
                  step={100}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>
          </div>
        );

      case 'llm_directional':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Min Edge (%)
                  <span className="block text-caption text-text-low">LLM vs market</span>
                </label>
                <input
                  type="number"
                  value={minEdgePct}
                  onChange={(e) => setMinEdgePct(parseFloat(e.target.value))}
                  min={5}
                  max={50}
                  step={5}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  Confidence Threshold
                  <span className="block text-caption text-text-low">Min LLM confidence</span>
                </label>
                <input
                  type="number"
                  value={llmConfidenceThreshold}
                  onChange={(e) => setLlmConfidenceThreshold(parseFloat(e.target.value))}
                  min={0.5}
                  max={1.0}
                  step={0.05}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block font-human text-label text-text-medium mb-2">
                  News Lookback (hrs)
                  <span className="block text-caption text-text-low">News window</span>
                </label>
                <input
                  type="number"
                  value={newsLookbackHours}
                  onChange={(e) => setNewsLookbackHours(parseInt(e.target.value))}
                  min={1}
                  max={72}
                  step={1}
                  className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-background border border-border">
      {/* Header */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="font-human text-h2 text-text-high">Trading Bot</h2>
            {botStatus && (
              <span className="px-3 py-1 bg-success/20 text-success font-machine text-caption rounded-full">
                RUNNING
              </span>
            )}
          </div>

          {botStatus ? (
            <button
              onClick={handleStop}
              disabled={loading}
              className="touch-target px-6 py-2 bg-error/20 text-error font-human text-body hover:bg-error/30 disabled:opacity-50 transition-colors"
            >
              Stop Bot
            </button>
          ) : (
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="touch-target px-6 py-2 bg-accent text-white font-human text-body hover:bg-accent/80 transition-colors"
            >
              {showConfig ? 'Cancel' : 'Start Bot'}
            </button>
          )}
        </div>

        {/* Status Info */}
        {botStatus && (
          <div className="mt-6 grid grid-cols-4 gap-4">
            <div className="p-4 bg-surface border border-border">
              <div className="font-human text-caption text-text-medium mb-1">Strategy</div>
              <div className="font-machine text-data text-text-high capitalize">
                {STRATEGIES[botStatus.strategy as keyof typeof STRATEGIES]?.icon}{' '}
                {STRATEGIES[botStatus.strategy as keyof typeof STRATEGIES]?.name || botStatus.strategy}
              </div>
            </div>
            <div className="p-4 bg-surface border border-border">
              <div className="font-human text-caption text-text-medium mb-1">Markets</div>
              <div className="font-machine text-data text-text-high">{botStatus.active_markets}</div>
            </div>
            <div className="p-4 bg-surface border border-border">
              <div className="font-human text-caption text-text-medium mb-1">Signals</div>
              <div className="font-machine text-data text-text-high">{botStatus.signal_count}</div>
            </div>
            <div className="p-4 bg-surface border border-border">
              <div className="font-human text-caption text-text-medium mb-1">Errors</div>
              <div className="font-machine text-data text-text-high text-error">{botStatus.error_count}</div>
            </div>
          </div>
        )}
      </div>

      {/* Config Panel */}
      {showConfig && !botStatus && (
        <div className="p-6 space-y-6">
          {/* Strategy Selector */}
          <div>
            <label className="block font-human text-label text-text-medium mb-3">
              Select Strategy
            </label>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.entries(STRATEGIES).map(([key, meta]) => (
                <button
                  key={key}
                  onClick={() => setStrategy(key)}
                  className={`relative touch-target p-4 border-2 transition-all ${
                    strategy === key
                      ? 'border-accent bg-accent/10'
                      : 'border-border bg-surface hover:border-accent/50'
                  }`}
                >
                  {meta.recommended && (
                    <span className="absolute top-2 right-2 px-2 py-0.5 bg-success text-white text-xs font-machine rounded">
                      ⭐
                    </span>
                  )}
                  <div className="text-2xl mb-2">{meta.icon}</div>
                  <div className="font-human text-body text-text-high mb-1">{meta.name}</div>
                  <div className="font-human text-caption text-text-medium">{meta.description}</div>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`text-xs font-machine px-2 py-0.5 rounded ${
                      meta.risk === 'Very Low' || meta.risk === 'Low' ? 'bg-success/20 text-success' :
                      meta.risk === 'Medium' ? 'bg-warning/20 text-warning' :
                      'bg-error/20 text-error'
                    }`}>
                      {meta.risk}
                    </span>
                    <span className="text-xs font-machine text-text-low">{meta.complexity}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* General Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-human text-label text-text-medium mb-2">
                Max Markets
              </label>
              <input
                type="number"
                value={maxMarkets}
                onChange={(e) => setMaxMarkets(parseInt(e.target.value))}
                min={1}
                max={50}
                className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            <div>
              <label className="block font-human text-label text-text-medium mb-2">
                Update Interval (seconds)
              </label>
              <input
                type="number"
                value={updateInterval}
                onChange={(e) => setUpdateInterval(parseInt(e.target.value))}
                min={1}
                max={60}
                className="w-full px-4 py-2 bg-surface border border-border font-machine text-data text-text-high focus:outline-none focus:border-accent transition-colors"
              />
            </div>
          </div>

          {/* Strategy-specific Config */}
          <div>
            <label className="block font-human text-label text-text-medium mb-3">
              Strategy Configuration
            </label>
            {renderStrategyConfig()}
          </div>

          {/* Start Button */}
          <button
            onClick={handleStart}
            disabled={loading}
            className="touch-target w-full py-4 bg-accent text-white font-human text-h3 hover:bg-accent/80 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Starting Bot...' : `Start ${STRATEGIES[strategy as keyof typeof STRATEGIES]?.name} Strategy`}
          </button>
        </div>
      )}
    </div>
  );
}
