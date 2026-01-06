// Data configuration
const DATASETS = {
  ablation: {
    title: 'ABLATION STUDY RESULTS',
    clusters: [
      { id: 'in_dist_follow', name: 'IN-DIST FOLLOW', points: [
        { label: 'π₀.₅', value: 85 }, { label: 'no WD', value: 84 },
        { label: 'no CE', value: 72 }, { label: 'no ME', value: 64 },
        { label: 'no ME/CE', value: 55 }
      ]},
      { id: 'in_dist_success', name: 'IN-DIST SUCCESS', points: [
        { label: 'π₀.₅', value: 80 }, { label: 'no WD', value: 79 },
        { label: 'no CE', value: 65 }, { label: 'no ME', value: 55 },
        { label: 'no ME/CE', value: 48 }
      ]},
      { id: 'ood_follow', name: 'OOD FOLLOW', points: [
        { label: 'π₀.₅', value: 94 }, { label: 'no WD', value: 80 },
        { label: 'no CE', value: 67 }, { label: 'no ME', value: 33 },
        { label: 'no ME/CE', value: 30 }
      ]},
      { id: 'ood_success', name: 'OOD SUCCESS', points: [
        { label: 'π₀.₅', value: 88 }, { label: 'no WD', value: 70 },
        { label: 'no CE', value: 48 }, { label: 'no ME', value: 32 },
        { label: 'no ME/CE', value: 28 }
      ]}
    ]
  },
  performance: {
    title: 'MODEL PERFORMANCE METRICS',
    clusters: [
      { id: 'accuracy', name: 'ACCURACY', points: [
        { label: 'Model A', value: 92 }, { label: 'Model B', value: 88 },
        { label: 'Model C', value: 85 }, { label: 'Model D', value: 79 },
        { label: 'Model E', value: 73 }, { label: 'Model F', value: 68 }
      ]},
      { id: 'latency', name: 'LATENCY (INV)', points: [
        { label: 'Model A', value: 45 }, { label: 'Model B', value: 78 },
        { label: 'Model C', value: 92 }, { label: 'Model D', value: 85 },
        { label: 'Model E', value: 88 }, { label: 'Model F', value: 95 }
      ]},
      { id: 'memory', name: 'MEMORY EFF', points: [
        { label: 'Model A', value: 60 }, { label: 'Model B', value: 72 },
        { label: 'Model C', value: 88 }, { label: 'Model D', value: 91 },
        { label: 'Model E', value: 85 }, { label: 'Model F', value: 78 }
      ]}
    ]
  }
};

// Monochrome palette based on rgba(65, 62, 62)
const COLORS = [
  'rgba(65, 62, 62, 1)',
  'rgba(65, 62, 62, 0.8)',
  'rgba(65, 62, 62, 0.6)',
  'rgba(65, 62, 62, 0.45)',
  'rgba(65, 62, 62, 0.3)',
  'rgba(65, 62, 62, 0.18)'
];
const CONFIG = { width: 1000, height: 400, padding: { top: 40, right: 40, bottom: 70, left: 60 } };
