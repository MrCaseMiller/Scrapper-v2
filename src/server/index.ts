/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  SNIPPET 2: API SERVER - Data Endpoints
 * ═══════════════════════════════════════════════════════════════════════════
 *
 *  ASCII FLOW:
 *  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 *  │   CLIENT    │────▶│   EXPRESS   │────▶│   DATA      │
 *  │   REQUEST   │     │   ROUTER    │     │   LAYER     │
 *  └─────────────┘     └─────────────┘     └─────────────┘
 *                             │
 *                             ▼
 *                      ┌─────────────┐
 *                      │  ENDPOINTS  │
 *                      │  /api/data  │
 *                      │  /api/config│
 *                      │  /api/export│
 *                      └─────────────┘
 */

import express, { Request, Response } from 'express';
import cors from 'cors';
import { GraphDataset, GraphConfig, DataCluster } from '../shared/types.js';

const app = express();
const PORT = 4000;

app.use(cors());
app.use(express.json());

// ═══════════════════════════════════════════════════════════════════════════
//  MOCK DATA - Simulating the ablation study chart from the image
// ═══════════════════════════════════════════════════════════════════════════

const MOCK_DATASETS: Record<string, GraphDataset> = {
  ablation: {
    title: 'ABLATION STUDY RESULTS',
    description: 'Evaluating training mixture compared to ablations excluding various data sources',
    clusters: [
      {
        id: 'in_dist_follow',
        name: 'IN-DISTRIBUTION FOLLOW RATE',
        points: [
          { label: 'π₀.₅', value: 85 },
          { label: 'no WD', value: 84 },
          { label: 'no CE', value: 72 },
          { label: 'no ME', value: 64 },
          { label: 'no ME/CE', value: 55 },
        ],
      },
      {
        id: 'in_dist_success',
        name: 'IN-DISTRIBUTION SUCCESS RATE',
        points: [
          { label: 'π₀.₅', value: 80 },
          { label: 'no WD', value: 79 },
          { label: 'no CE', value: 65 },
          { label: 'no ME', value: 55 },
          { label: 'no ME/CE', value: 48 },
        ],
      },
      {
        id: 'ood_follow',
        name: 'OOD FOLLOW RATE',
        points: [
          { label: 'π₀.₅', value: 94 },
          { label: 'no WD', value: 80 },
          { label: 'no CE', value: 67 },
          { label: 'no ME', value: 33 },
          { label: 'no ME/CE', value: 30 },
        ],
      },
      {
        id: 'ood_success',
        name: 'OOD SUCCESS RATE',
        points: [
          { label: 'π₀.₅', value: 88 },
          { label: 'no WD', value: 70 },
          { label: 'no CE', value: 48 },
          { label: 'no ME', value: 32 },
          { label: 'no ME/CE', value: 28 },
        ],
      },
    ],
    series: [
      { key: 'baseline', label: 'π₀.₅', color: '#1a1a1a' },
      { key: 'no_wd', label: 'no WD', color: '#404040' },
      { key: 'no_ce', label: 'no CE', color: '#666666' },
      { key: 'no_me', label: 'no ME', color: '#8c8c8c' },
      { key: 'no_me_ce', label: 'no ME/CE', color: '#b3b3b3' },
    ],
  },
  performance: {
    title: 'MODEL PERFORMANCE METRICS',
    description: 'Comparing performance across different model configurations',
    clusters: [
      {
        id: 'accuracy',
        name: 'ACCURACY',
        points: [
          { label: 'Model A', value: 92 },
          { label: 'Model B', value: 88 },
          { label: 'Model C', value: 85 },
          { label: 'Model D', value: 79 },
          { label: 'Model E', value: 73 },
          { label: 'Model F', value: 68 },
        ],
      },
      {
        id: 'latency',
        name: 'LATENCY (INV)',
        points: [
          { label: 'Model A', value: 45 },
          { label: 'Model B', value: 78 },
          { label: 'Model C', value: 92 },
          { label: 'Model D', value: 85 },
          { label: 'Model E', value: 88 },
          { label: 'Model F', value: 95 },
        ],
      },
      {
        id: 'memory',
        name: 'MEMORY EFFICIENCY',
        points: [
          { label: 'Model A', value: 60 },
          { label: 'Model B', value: 72 },
          { label: 'Model C', value: 88 },
          { label: 'Model D', value: 91 },
          { label: 'Model E', value: 85 },
          { label: 'Model F', value: 78 },
        ],
      },
    ],
    series: [
      { key: 'model_a', label: 'Model A', color: '#1a1a1a' },
      { key: 'model_b', label: 'Model B', color: '#333333' },
      { key: 'model_c', label: 'Model C', color: '#4d4d4d' },
      { key: 'model_d', label: 'Model D', color: '#666666' },
      { key: 'model_e', label: 'Model E', color: '#808080' },
      { key: 'model_f', label: 'Model F', color: '#999999' },
    ],
  },
};

const DEFAULT_CONFIG: GraphConfig = {
  width: 1200,
  height: 500,
  padding: { top: 40, right: 40, bottom: 80, left: 60 },
  style: 'bar',
  showGrid: true,
  showLegend: true,
  animated: true,
};

// ═══════════════════════════════════════════════════════════════════════════
//  ENDPOINT: GET /api/data/:datasetId
//  Returns graph data for a specific dataset
// ═══════════════════════════════════════════════════════════════════════════

app.get('/api/data/:datasetId', (req: Request, res: Response) => {
  const { datasetId } = req.params;
  const dataset = MOCK_DATASETS[datasetId];

  if (!dataset) {
    res.status(404).json({
      error: 'Dataset not found',
      available: Object.keys(MOCK_DATASETS),
    });
    return;
  }

  res.json({ success: true, data: dataset });
});

// ═══════════════════════════════════════════════════════════════════════════
//  ENDPOINT: GET /api/data
//  Returns all available datasets
// ═══════════════════════════════════════════════════════════════════════════

app.get('/api/data', (_req: Request, res: Response) => {
  const summary = Object.entries(MOCK_DATASETS).map(([id, dataset]) => ({
    id,
    title: dataset.title,
    clusterCount: dataset.clusters.length,
    pointsPerCluster: dataset.clusters[0]?.points.length || 0,
  }));

  res.json({ success: true, datasets: summary });
});

// ═══════════════════════════════════════════════════════════════════════════
//  ENDPOINT: GET /api/config
//  Returns default graph configuration
// ═══════════════════════════════════════════════════════════════════════════

app.get('/api/config', (_req: Request, res: Response) => {
  res.json({ success: true, config: DEFAULT_CONFIG });
});

// ═══════════════════════════════════════════════════════════════════════════
//  ENDPOINT: POST /api/config
//  Updates graph configuration
// ═══════════════════════════════════════════════════════════════════════════

app.post('/api/config', (req: Request, res: Response) => {
  const newConfig = { ...DEFAULT_CONFIG, ...req.body };
  res.json({ success: true, config: newConfig });
});

// ═══════════════════════════════════════════════════════════════════════════
//  ENDPOINT: POST /api/cluster
//  Returns data for a specific cluster (for tooltip/detail views)
// ═══════════════════════════════════════════════════════════════════════════

app.post('/api/cluster', (req: Request, res: Response) => {
  const { datasetId, clusterId } = req.body;
  const dataset = MOCK_DATASETS[datasetId];

  if (!dataset) {
    res.status(404).json({ error: 'Dataset not found' });
    return;
  }

  const cluster = dataset.clusters.find((c: DataCluster) => c.id === clusterId);

  if (!cluster) {
    res.status(404).json({ error: 'Cluster not found' });
    return;
  }

  // Calculate statistics
  const values = cluster.points.map((p) => p.value);
  const stats = {
    min: Math.min(...values),
    max: Math.max(...values),
    avg: values.reduce((a, b) => a + b, 0) / values.length,
    range: Math.max(...values) - Math.min(...values),
  };

  res.json({ success: true, cluster, stats });
});

// ═══════════════════════════════════════════════════════════════════════════
//  ENDPOINT: POST /api/export
//  Generates export-ready data in various formats
// ═══════════════════════════════════════════════════════════════════════════

app.post('/api/export', (req: Request, res: Response) => {
  const { datasetId, format } = req.body;
  const dataset = MOCK_DATASETS[datasetId];

  if (!dataset) {
    res.status(404).json({ error: 'Dataset not found' });
    return;
  }

  switch (format) {
    case 'csv': {
      const headers = ['Cluster', ...dataset.clusters[0].points.map((p) => p.label)];
      const rows = dataset.clusters.map((c) => [
        c.name,
        ...c.points.map((p) => p.value.toString()),
      ]);
      const csv = [headers, ...rows].map((r) => r.join(',')).join('\n');
      res.json({ success: true, format: 'csv', content: csv });
      break;
    }
    case 'json':
    default:
      res.json({ success: true, format: 'json', content: dataset });
  }
});

// ═══════════════════════════════════════════════════════════════════════════
//  START SERVER
// ═══════════════════════════════════════════════════════════════════════════

app.listen(PORT, () => {
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════╗
║  BRUTALIST GRAPH API SERVER                                               ║
║  ─────────────────────────────────────────────────────────────────────────║
║  PORT: ${PORT}                                                              ║
║  ENDPOINTS:                                                               ║
║    GET  /api/data          - List all datasets                            ║
║    GET  /api/data/:id      - Get specific dataset                         ║
║    GET  /api/config        - Get default config                           ║
║    POST /api/config        - Update config                                ║
║    POST /api/cluster       - Get cluster details                          ║
║    POST /api/export        - Export data (csv/json)                       ║
╚═══════════════════════════════════════════════════════════════════════════╝
  `);
});

export default app;
