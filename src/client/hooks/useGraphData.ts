/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  CUSTOM HOOK: useGraphData
 * ═══════════════════════════════════════════════════════════════════════════
 *
 *  DATA FLOW:
 *  ┌──────────┐    ┌──────────┐    ┌──────────┐
 *  │  FETCH   │───▶│  PARSE   │───▶│  STATE   │
 *  │  API     │    │  DATA    │    │  UPDATE  │
 *  └──────────┘    └──────────┘    └──────────┘
 */

import { useState, useEffect, useCallback } from 'react';
import { GraphDataset, GraphConfig } from '../../shared/types';

interface UseGraphDataReturn {
  dataset: GraphDataset | null;
  config: GraphConfig | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  updateConfig: (updates: Partial<GraphConfig>) => void;
}

const DEFAULT_CONFIG: GraphConfig = {
  width: 1200,
  height: 500,
  padding: { top: 40, right: 40, bottom: 80, left: 60 },
  style: 'bar',
  showGrid: true,
  showLegend: true,
  animated: true,
};

export function useGraphData(datasetId: string): UseGraphDataReturn {
  const [dataset, setDataset] = useState<GraphDataset | null>(null);
  const [config, setConfig] = useState<GraphConfig | null>(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/data/${datasetId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch dataset`);
      }
      const result = await response.json();
      if (result.success) {
        setDataset(result.data);
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  const updateConfig = useCallback((updates: Partial<GraphConfig>) => {
    setConfig((prev) => (prev ? { ...prev, ...updates } : null));
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    dataset,
    config,
    loading,
    error,
    refetch: fetchData,
    updateConfig,
  };
}
