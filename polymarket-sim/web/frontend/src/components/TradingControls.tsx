/**
 * Trading bot controls component
 */

'use client';

import { useState, useEffect } from 'react';
import { botAPI, marketsAPI } from '../utils/api';

interface TradingControlsProps {
  onBotStatusChange?: (status: any) => void;
}

export default function TradingControls({ onBotStatusChange }: TradingControlsProps) {
  const [botStatus, setBotStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  // Config state
  const [strategy, setStrategy] = useState('threshold');
  const [maxMarkets, setMaxMarkets] = useState(5);
  const [updateInterval, setUpdateInterval] = useState(5);
  const [buyBelow, setBuyBelow] = useState(0.3);
  const [sellAbove, setSellAbove] = useState(0.7);
  const [positionSize, setPositionSize] = useState(100);

  useEffect(() => {
    loadBotStatus();
    const interval = setInterval(loadBotStatus, 3000); // Check every 3s
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
      // Bot not running
      setBotStatus(null);
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      const config = {
        strategy,
        max_markets: maxMarkets,
        update_interval: updateInterval,
        strategy_params: {
          buy_below: buyBelow,
          sell_above: sellAbove,
          position_size: positionSize,
        },
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

  return (
    <div className="bg-bg-secondary rounded-lg">
      {/* Header */}
      <div className="p-6">
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
              className="touch-target px-4 py-2 bg-error/20 text-error rounded-lg font-human text-body disabled:opacity-50"
            >
              Stop
            </button>
          ) : (
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="touch-target px-4 py-2 bg-accent text-white rounded-lg font-human text-body"
            >
              {showConfig ? 'Cancel' : 'Start Bot'}
            </button>
          )}
        </div>

        {/* Status Info */}
        {botStatus && (
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div>
              <div className="font-human text-caption text-text-medium mb-1">Strategy</div>
              <div className="font-machine text-data text-text-high capitalize">{botStatus.strategy}</div>
            </div>
            <div>
              <div className="font-human text-caption text-text-medium mb-1">Markets</div>
              <div className="font-machine text-data text-text-high">{botStatus.active_markets}</div>
            </div>
            <div>
              <div className="font-human text-caption text-text-medium mb-1">Signals</div>
              <div className="font-machine text-data text-text-high">{botStatus.signal_count}</div>
            </div>
            <div>
              <div className="font-human text-caption text-text-medium mb-1">Errors</div>
              <div className="font-machine text-data text-text-high">{botStatus.error_count}</div>
            </div>
          </div>
        )}
      </div>

      {/* Config Panel */}
      {showConfig && !botStatus && (
        <div className="px-6 pb-6 space-y-6">
          {/* Strategy Selector */}
          <div>
            <label className="block font-human text-label text-text-medium mb-2">
              Strategy
            </label>
            <div className="grid grid-cols-3 gap-2">
              {['threshold', 'mean_reversion', 'manual'].map((s) => (
                <button
                  key={s}
                  onClick={() => setStrategy(s)}
                  className={`touch-target px-4 py-2 rounded-lg font-human text-body transition-colors ${
                    strategy === s
                      ? 'bg-accent text-white'
                      : 'bg-bg-primary text-text-medium'
                  }`}
                >
                  {s.replace('_', ' ')}
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
                max={20}
                className="w-full px-4 py-2 bg-bg-primary rounded-lg font-machine text-data text-text-high focus:outline-none focus:bg-white/5 transition-colors"
              />
            </div>

            <div>
              <label className="block font-human text-label text-text-medium mb-2">
                Update Interval (s)
              </label>
              <input
                type="number"
                value={updateInterval}
                onChange={(e) => setUpdateInterval(parseInt(e.target.value))}
                min={1}
                max={60}
                className="w-full px-4 py-2 bg-bg-primary rounded-lg font-machine text-data text-text-high focus:outline-none focus:bg-white/5 transition-colors"
              />
            </div>
          </div>

          {/* Strategy-specific settings */}
          {strategy === 'threshold' && (
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
                  className="w-full px-4 py-2 bg-bg-primary rounded-lg font-machine text-data text-text-high focus:outline-none focus:bg-white/5 transition-colors"
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
                  className="w-full px-4 py-2 bg-bg-primary rounded-lg font-machine text-data text-text-high focus:outline-none focus:bg-white/5 transition-colors"
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
                  className="w-full px-4 py-2 bg-bg-primary rounded-lg font-machine text-data text-text-high focus:outline-none focus:bg-white/5 transition-colors"
                />
              </div>
            </div>
          )}

          {/* Start Button */}
          <button
            onClick={handleStart}
            disabled={loading}
            className="touch-target w-full py-3 bg-accent text-white rounded-lg font-human text-body disabled:opacity-50"
          >
            {loading ? 'Starting...' : 'Start Trading'}
          </button>
        </div>
      )}
    </div>
  );
}
