/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  DEMO APPLICATION
 * ═══════════════════════════════════════════════════════════════════════════
 *
 *  LAYOUT:
 *  ┌─────────────────────────────────────────────────────────────────────┐
 *  │  ╔═══════════════════════════════════════════════════════════════╗  │
 *  │  ║  BRUTALIST GRAPH SYSTEM                                       ║  │
 *  │  ╚═══════════════════════════════════════════════════════════════╝  │
 *  │                                                                     │
 *  │  [ABLATION] [PERFORMANCE]                                           │
 *  │                                                                     │
 *  │  ┌─────────────────────────────────────────────────────────────┐   │
 *  │  │                                                             │   │
 *  │  │              GRAPH COMPONENT                                │   │
 *  │  │                                                             │   │
 *  │  └─────────────────────────────────────────────────────────────┘   │
 *  │                                                                     │
 *  └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState } from 'react';
import { BrutalistGraph } from './components/BrutalistGraph';

const DATASETS = [
  { id: 'ablation', label: 'ABLATION STUDY' },
  { id: 'performance', label: 'PERFORMANCE' },
];

export const App: React.FC = () => {
  const [activeDataset, setActiveDataset] = useState('ablation');

  return (
    <div className="app">
      <header className="app-header">
        <h1>BRUTALIST GRAPH SYSTEM</h1>
        <p>INTERACTIVE DATA VISUALIZATION / GRAYSCALE MINIMALIST UI</p>
      </header>

      <nav className="dataset-nav">
        {DATASETS.map((ds) => (
          <button
            key={ds.id}
            className={`btn ${activeDataset === ds.id ? 'active' : ''}`}
            onClick={() => setActiveDataset(ds.id)}
          >
            {ds.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        <BrutalistGraph key={activeDataset} datasetId={activeDataset} />
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <span>SNIPPET 1: React Component</span>
          <span>│</span>
          <span>SNIPPET 2: API Server</span>
          <span>│</span>
          <span>SNIPPET 3: Renderers</span>
        </div>
      </footer>

      <style>{`
        .app {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        .app-header {
          padding: 32px;
          background: #1a1a1a;
          color: #f5f5f5;
          text-align: center;
          border-bottom: 4px solid #1a1a1a;
        }

        .app-header h1 {
          font-size: 24px;
          font-weight: 900;
          letter-spacing: 4px;
          margin-bottom: 8px;
        }

        .app-header p {
          font-size: 12px;
          letter-spacing: 2px;
          color: #999;
        }

        .dataset-nav {
          display: flex;
          gap: 0;
          padding: 0 20px;
          background: #e8e8e8;
          border-bottom: 3px solid #1a1a1a;
        }

        .dataset-nav .btn {
          border-radius: 0;
          border-left: none;
          border-right: 2px solid #1a1a1a;
        }

        .dataset-nav .btn:first-child {
          border-left: 2px solid #1a1a1a;
        }

        .app-main {
          flex: 1;
          padding: 20px;
          background: #f5f5f5;
        }

        .app-footer {
          padding: 16px;
          background: #1a1a1a;
          color: #666;
          text-align: center;
          border-top: 3px solid #1a1a1a;
        }

        .footer-content {
          display: flex;
          justify-content: center;
          gap: 16px;
          font-size: 11px;
          letter-spacing: 1px;
        }
      `}</style>
    </div>
  );
};

export default App;
