/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  SHARED TYPES - Graph Data Structures
 * ═══════════════════════════════════════════════════════════════════════════
 */

export type GraphStyle = 'bar' | 'line' | 'radar' | 'stacked';

export interface DataPoint {
  label: string;
  value: number;
  metadata?: Record<string, unknown>;
}

export interface DataCluster {
  id: string;
  name: string;
  points: DataPoint[];
}

export interface GraphDataset {
  title: string;
  description?: string;
  clusters: DataCluster[];
  series: SeriesConfig[];
}

export interface SeriesConfig {
  key: string;
  label: string;
  color: string;
}

export interface TooltipData {
  visible: boolean;
  x: number;
  y: number;
  cluster: DataCluster | null;
  pointIndex: number;
}

export interface GraphConfig {
  width: number;
  height: number;
  padding: { top: number; right: number; bottom: number; left: number };
  style: GraphStyle;
  showGrid: boolean;
  showLegend: boolean;
  animated: boolean;
}

export interface Theme {
  name: string;
  background: string;
  foreground: string;
  grid: string;
  border: string;
  text: string;
  textMuted: string;
  bars: string[];
  tooltip: {
    background: string;
    border: string;
    text: string;
  };
}

export const BRUTALIST_THEME: Theme = {
  name: 'brutalist',
  background: '#f5f5f5',
  foreground: '#1a1a1a',
  grid: '#e0e0e0',
  border: '#1a1a1a',
  text: '#1a1a1a',
  textMuted: '#666666',
  bars: ['#1a1a1a', '#404040', '#666666', '#8c8c8c', '#b3b3b3', '#d9d9d9'],
  tooltip: {
    background: '#ffffff',
    border: '#1a1a1a',
    text: '#1a1a1a',
  },
};

export const DARK_BRUTALIST_THEME: Theme = {
  name: 'dark-brutalist',
  background: '#1a1a1a',
  foreground: '#f5f5f5',
  grid: '#333333',
  border: '#f5f5f5',
  text: '#f5f5f5',
  textMuted: '#999999',
  bars: ['#f5f5f5', '#cccccc', '#999999', '#666666', '#4d4d4d', '#333333'],
  tooltip: {
    background: '#2a2a2a',
    border: '#f5f5f5',
    text: '#f5f5f5',
  },
};
