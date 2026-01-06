/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  SNIPPET 1: BRUTALIST GRAPH COMPONENT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 *  COMPONENT STRUCTURE:
 *  ┌─────────────────────────────────────────────────────────────────────┐
 *  │  ┌─────────────────────────────────────────────────────────────┐   │
 *  │  │  HEADER: Title + Window Controls                            │   │
 *  │  └─────────────────────────────────────────────────────────────┘   │
 *  │  ┌─────────────────────────────────────────────────────────────┐   │
 *  │  │  TOOLBAR: Graph Type | Theme | Export Options               │   │
 *  │  └─────────────────────────────────────────────────────────────┘   │
 *  │  ┌─────────────────────────────────────────────────────────────┐   │
 *  │  │                                                             │   │
 *  │  │              SVG CHART AREA                                 │   │
 *  │  │              (Dynamic Render)                               │   │
 *  │  │                                                             │   │
 *  │  └─────────────────────────────────────────────────────────────┘   │
 *  │  ┌─────────────────────────────────────────────────────────────┐   │
 *  │  │  LEGEND: Series labels with swatches                        │   │
 *  │  └─────────────────────────────────────────────────────────────┘   │
 *  │                                                                     │
 *  │  ┌──────────────────┐  (Floating Tooltip on hover)                 │
 *  │  │  CLUSTER NAME    │                                              │
 *  │  │  ─────────────   │                                              │
 *  │  │  █ label: 94%    │                                              │
 *  │  │  ▓ label: 80%    │                                              │
 *  │  └──────────────────┘                                              │
 *  └─────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import { useGraphData } from '../hooks/useGraphData';
import { renderGraph } from '../renderers';
import {
  GraphStyle,
  TooltipData,
  Theme,
  BRUTALIST_THEME,
  DARK_BRUTALIST_THEME,
  DataCluster,
} from '../../shared/types';
import '../styles/brutalist.css';

interface BrutalistGraphProps {
  datasetId: string;
  initialStyle?: GraphStyle;
  showToolbar?: boolean;
}

export const BrutalistGraph: React.FC<BrutalistGraphProps> = ({
  datasetId,
  initialStyle = 'bar',
  showToolbar = true,
}) => {
  const { dataset, config, loading, error, updateConfig } = useGraphData(datasetId);
  const [graphStyle, setGraphStyle] = useState<GraphStyle>(initialStyle);
  const [isDarkTheme, setIsDarkTheme] = useState(false);
  const [tooltip, setTooltip] = useState<TooltipData>({
    visible: false,
    x: 0,
    y: 0,
    cluster: null,
    pointIndex: -1,
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const svgContainerRef = useRef<HTMLDivElement>(null);

  const theme: Theme = isDarkTheme ? DARK_BRUTALIST_THEME : BRUTALIST_THEME;

  // Update config when style changes
  useEffect(() => {
    updateConfig({ style: graphStyle });
  }, [graphStyle, updateConfig]);

  // Handle mouse events on SVG elements
  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      const target = e.target as SVGElement;
      const clusterId = target.getAttribute('data-cluster');
      const pointIndex = target.getAttribute('data-point');

      if (clusterId && pointIndex !== null && dataset) {
        const cluster = dataset.clusters.find((c) => c.id === clusterId);
        if (cluster) {
          const rect = containerRef.current?.getBoundingClientRect();
          if (rect) {
            setTooltip({
              visible: true,
              x: e.clientX - rect.left + 20,
              y: e.clientY - rect.top - 10,
              cluster,
              pointIndex: parseInt(pointIndex, 10),
            });
          }
        }
      }
    },
    [dataset]
  );

  const handleMouseLeave = useCallback(() => {
    setTooltip((prev) => ({ ...prev, visible: false }));
  }, []);

  // Render the SVG chart
  const chartSVG = useMemo(() => {
    if (!dataset || !config) return '';
    return renderGraph(dataset.clusters, { ...config, style: graphStyle }, theme);
  }, [dataset, config, graphStyle, theme]);

  // Export handlers
  const handleExportSVG = useCallback(() => {
    if (!chartSVG) return;
    const blob = new Blob([chartSVG], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${datasetId}-chart.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }, [chartSVG, datasetId]);

  const handleExportPNG = useCallback(() => {
    if (!svgContainerRef.current) return;
    const svg = svgContainerRef.current.querySelector('svg');
    if (!svg) return;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const img = new Image();
    img.onload = () => {
      canvas.width = img.width * 2;
      canvas.height = img.height * 2;
      ctx.scale(2, 2);
      ctx.drawImage(img, 0, 0);
      const a = document.createElement('a');
      a.href = canvas.toDataURL('image/png');
      a.download = `${datasetId}-chart.png`;
      a.click();
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  }, [datasetId]);

  // Loading state
  if (loading) {
    return (
      <div className="graph-container" data-theme={isDarkTheme ? 'dark' : 'light'}>
        <div className="loading-state">
          <div className="loading-spinner" />
          <span>LOADING DATA...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="graph-container" data-theme={isDarkTheme ? 'dark' : 'light'}>
        <div className="error-state">
          <span className="error-message">ERROR: {error}</span>
          <button className="btn" onClick={() => window.location.reload()}>
            RETRY
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="graph-container"
      ref={containerRef}
      data-theme={isDarkTheme ? 'dark' : 'light'}
    >
      {/* Header */}
      <div className="graph-header">
        <span className="graph-title">{dataset?.title || 'GRAPH'}</span>
        <div className="graph-controls">
          <button className="btn btn-icon" onClick={() => setIsDarkTheme(!isDarkTheme)}>
            {isDarkTheme ? '☀' : '☾'}
          </button>
        </div>
      </div>

      {/* Toolbar */}
      {showToolbar && (
        <div className="toolbar">
          <div className="toolbar-group">
            <span className="toolbar-label">TYPE:</span>
            <select
              className="brutalist-select"
              value={graphStyle}
              onChange={(e) => setGraphStyle(e.target.value as GraphStyle)}
            >
              <option value="bar">BAR</option>
              <option value="line">LINE</option>
              <option value="radar">RADAR</option>
              <option value="stacked">STACKED</option>
            </select>
          </div>

          <div className="toolbar-group">
            <span className="toolbar-label">EXPORT:</span>
            <button className="btn" onClick={handleExportSVG}>
              SVG
            </button>
            <button className="btn" onClick={handleExportPNG}>
              PNG
            </button>
          </div>
        </div>
      )}

      {/* Chart Area */}
      <div
        className="graph-body"
        ref={svgContainerRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        dangerouslySetInnerHTML={{ __html: chartSVG }}
      />

      {/* Legend */}
      {config?.showLegend && dataset && (
        <div className="legend">
          {dataset.clusters[0]?.points.map((point, i) => (
            <div key={point.label} className="legend-item">
              <div
                className="legend-swatch"
                style={{ backgroundColor: theme.bars[i % theme.bars.length] }}
              />
              <span>{point.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tooltip */}
      <Tooltip tooltip={tooltip} theme={theme} />
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
//  TOOLTIP COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface TooltipProps {
  tooltip: TooltipData;
  theme: Theme;
}

const Tooltip: React.FC<TooltipProps> = ({ tooltip, theme }) => {
  if (!tooltip.cluster) return null;

  const maxValue = Math.max(...tooltip.cluster.points.map((p) => p.value));

  return (
    <div
      className={`tooltip ${tooltip.visible ? 'visible' : ''}`}
      style={{
        left: tooltip.x,
        top: tooltip.y,
      }}
    >
      <div className="tooltip-header">{tooltip.cluster.name}</div>
      <div className="tooltip-body">
        {tooltip.cluster.points.map((point, i) => (
          <div key={point.label} className="tooltip-row">
            <div className="tooltip-label">
              <div
                className="tooltip-swatch"
                style={{ backgroundColor: theme.bars[i % theme.bars.length] }}
              />
              <span>{point.label}</span>
            </div>
            <span className="tooltip-value">{point.value}%</span>
          </div>
        ))}
        <div
          className="tooltip-bar"
          style={{
            width: `${(tooltip.cluster.points[tooltip.pointIndex]?.value / maxValue) * 100}%`,
          }}
        />
      </div>
    </div>
  );
};

export default BrutalistGraph;
