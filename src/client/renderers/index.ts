/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  SNIPPET 3: GRAPH RENDERERS
 * ═══════════════════════════════════════════════════════════════════════════
 *
 *  RENDER PIPELINE:
 *  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
 *  │   DATA   │───▶│  SCALE   │───▶│  RENDER  │───▶│   SVG    │
 *  │ CLUSTERS │    │ COMPUTE  │    │  ENGINE  │    │ OUTPUT   │
 *  └──────────┘    └──────────┘    └──────────┘    └──────────┘
 *
 *  SUPPORTED STYLES:
 *  ┌─────────────────────────────────────────────────────────────────────┐
 *  │  BAR       │  LINE      │  RADAR     │  STACKED   │                │
 *  │  ██ ▓▓ ▒▒  │  ●─●─●─●   │    /\      │  ████████  │                │
 *  │  ██ ▓▓ ▒▒  │ /  \  /\   │   /  \     │  ▓▓▓▓▓▓▓▓  │                │
 *  │  ██ ▓▓     │●    ●●  ●  │  ●────●    │  ▒▒▒▒▒▒▒▒  │                │
 *  └─────────────────────────────────────────────────────────────────────┘
 */

import { DataCluster, GraphConfig, Theme, GraphStyle } from '../../shared/types';

// ═══════════════════════════════════════════════════════════════════════════
//  SCALE UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

export function computeScale(
  clusters: DataCluster[],
  config: GraphConfig
): { xScale: (i: number) => number; yScale: (v: number) => number; maxValue: number } {
  const allValues = clusters.flatMap((c) => c.points.map((p) => p.value));
  const maxValue = Math.ceil(Math.max(...allValues) / 10) * 10;

  const chartWidth = config.width - config.padding.left - config.padding.right;
  const chartHeight = config.height - config.padding.top - config.padding.bottom;

  const xScale = (clusterIndex: number) =>
    config.padding.left + (clusterIndex + 0.5) * (chartWidth / clusters.length);

  const yScale = (value: number) =>
    config.height - config.padding.bottom - (value / maxValue) * chartHeight;

  return { xScale, yScale, maxValue };
}

// ═══════════════════════════════════════════════════════════════════════════
//  BAR CHART RENDERER
// ═══════════════════════════════════════════════════════════════════════════

export function renderBarChart(
  clusters: DataCluster[],
  config: GraphConfig,
  theme: Theme
): string {
  const { xScale, yScale, maxValue } = computeScale(clusters, config);
  const chartHeight = config.height - config.padding.top - config.padding.bottom;
  const clusterWidth = (config.width - config.padding.left - config.padding.right) / clusters.length;
  const barPadding = 4;
  const maxBarsPerCluster = Math.max(...clusters.map((c) => c.points.length));
  const barWidth = Math.max(8, (clusterWidth - barPadding * 2) / maxBarsPerCluster - 4);

  let svg = `
    <svg
      width="${config.width}"
      height="${config.height}"
      viewBox="0 0 ${config.width} ${config.height}"
      class="brutalist-chart"
    >
      <defs>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="2" dy="2" stdDeviation="0" flood-color="${theme.border}" flood-opacity="0.3"/>
        </filter>
      </defs>

      <!-- Background -->
      <rect width="100%" height="100%" fill="${theme.background}"/>
  `;

  // Grid lines
  if (config.showGrid) {
    for (let i = 0; i <= 10; i++) {
      const y = config.padding.top + (i / 10) * chartHeight;
      const value = maxValue - (i / 10) * maxValue;
      svg += `
        <line
          x1="${config.padding.left}"
          y1="${y}"
          x2="${config.width - config.padding.right}"
          y2="${y}"
          stroke="${theme.grid}"
          stroke-width="1"
          stroke-dasharray="${i % 2 === 0 ? 'none' : '4,4'}"
        />
        <text
          x="${config.padding.left - 10}"
          y="${y + 4}"
          text-anchor="end"
          fill="${theme.textMuted}"
          font-family="monospace"
          font-size="11"
        >${value}%</text>
      `;
    }
  }

  // Bars for each cluster
  clusters.forEach((cluster, ci) => {
    const clusterX = xScale(ci);
    const startX = clusterX - (cluster.points.length * (barWidth + 2)) / 2;

    cluster.points.forEach((point, pi) => {
      const barHeight = ((config.height - config.padding.bottom) - yScale(point.value));
      const x = startX + pi * (barWidth + 2);
      const y = yScale(point.value);
      const color = theme.bars[pi % theme.bars.length];

      svg += `
        <rect
          class="bar"
          data-cluster="${cluster.id}"
          data-point="${pi}"
          data-value="${point.value}"
          data-label="${point.label}"
          x="${x}"
          y="${y}"
          width="${barWidth}"
          height="${barHeight}"
          fill="${color}"
          stroke="${theme.border}"
          stroke-width="1"
          filter="url(#shadow)"
        >
          <animate
            attributeName="height"
            from="0"
            to="${barHeight}"
            dur="0.5s"
            fill="freeze"
          />
          <animate
            attributeName="y"
            from="${config.height - config.padding.bottom}"
            to="${y}"
            dur="0.5s"
            fill="freeze"
          />
        </rect>
      `;
    });

    // Cluster label
    svg += `
      <text
        x="${clusterX}"
        y="${config.height - config.padding.bottom + 40}"
        text-anchor="middle"
        fill="${theme.text}"
        font-family="monospace"
        font-size="10"
        font-weight="bold"
        letter-spacing="0.5"
      >${cluster.name}</text>
    `;
  });

  // Axis lines
  svg += `
    <line
      x1="${config.padding.left}"
      y1="${config.padding.top}"
      x2="${config.padding.left}"
      y2="${config.height - config.padding.bottom}"
      stroke="${theme.border}"
      stroke-width="2"
    />
    <line
      x1="${config.padding.left}"
      y1="${config.height - config.padding.bottom}"
      x2="${config.width - config.padding.right}"
      y2="${config.height - config.padding.bottom}"
      stroke="${theme.border}"
      stroke-width="2"
    />
  `;

  svg += '</svg>';
  return svg;
}

// ═══════════════════════════════════════════════════════════════════════════
//  LINE CHART RENDERER
// ═══════════════════════════════════════════════════════════════════════════

export function renderLineChart(
  clusters: DataCluster[],
  config: GraphConfig,
  theme: Theme
): string {
  const { yScale, maxValue } = computeScale(clusters, config);
  const chartHeight = config.height - config.padding.top - config.padding.bottom;
  const chartWidth = config.width - config.padding.left - config.padding.right;

  // For line chart, we plot series across clusters
  const numPoints = clusters.length;
  const pointSpacing = chartWidth / (numPoints - 1 || 1);

  let svg = `
    <svg
      width="${config.width}"
      height="${config.height}"
      viewBox="0 0 ${config.width} ${config.height}"
      class="brutalist-chart line-chart"
    >
      <rect width="100%" height="100%" fill="${theme.background}"/>
  `;

  // Grid
  if (config.showGrid) {
    for (let i = 0; i <= 10; i++) {
      const y = config.padding.top + (i / 10) * chartHeight;
      const value = maxValue - (i / 10) * maxValue;
      svg += `
        <line
          x1="${config.padding.left}"
          y1="${y}"
          x2="${config.width - config.padding.right}"
          y2="${y}"
          stroke="${theme.grid}"
          stroke-width="1"
        />
        <text
          x="${config.padding.left - 10}"
          y="${y + 4}"
          text-anchor="end"
          fill="${theme.textMuted}"
          font-family="monospace"
          font-size="11"
        >${value}%</text>
      `;
    }

    // Vertical grid
    clusters.forEach((_, i) => {
      const x = config.padding.left + i * pointSpacing;
      svg += `
        <line
          x1="${x}"
          y1="${config.padding.top}"
          x2="${x}"
          y2="${config.height - config.padding.bottom}"
          stroke="${theme.grid}"
          stroke-width="1"
        />
      `;
    });
  }

  // Draw lines for each series (point index across clusters)
  const numSeries = clusters[0]?.points.length || 0;

  for (let si = 0; si < numSeries; si++) {
    const color = theme.bars[si % theme.bars.length];
    let pathD = '';

    clusters.forEach((cluster, ci) => {
      const x = config.padding.left + ci * pointSpacing;
      const y = yScale(cluster.points[si]?.value || 0);
      pathD += ci === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
    });

    svg += `
      <path
        d="${pathD}"
        fill="none"
        stroke="${color}"
        stroke-width="3"
        stroke-linecap="square"
        class="line-path"
        data-series="${si}"
      />
    `;

    // Points
    clusters.forEach((cluster, ci) => {
      const x = config.padding.left + ci * pointSpacing;
      const y = yScale(cluster.points[si]?.value || 0);
      svg += `
        <rect
          x="${x - 5}"
          y="${y - 5}"
          width="10"
          height="10"
          fill="${theme.background}"
          stroke="${color}"
          stroke-width="2"
          class="data-point"
          data-cluster="${cluster.id}"
          data-point="${si}"
          data-value="${cluster.points[si]?.value}"
        />
      `;
    });
  }

  // X-axis labels
  clusters.forEach((cluster, i) => {
    const x = config.padding.left + i * pointSpacing;
    svg += `
      <text
        x="${x}"
        y="${config.height - config.padding.bottom + 30}"
        text-anchor="middle"
        fill="${theme.text}"
        font-family="monospace"
        font-size="9"
        font-weight="bold"
      >${cluster.name}</text>
    `;
  });

  // Axes
  svg += `
    <line
      x1="${config.padding.left}"
      y1="${config.padding.top}"
      x2="${config.padding.left}"
      y2="${config.height - config.padding.bottom}"
      stroke="${theme.border}"
      stroke-width="2"
    />
    <line
      x1="${config.padding.left}"
      y1="${config.height - config.padding.bottom}"
      x2="${config.width - config.padding.right}"
      y2="${config.height - config.padding.bottom}"
      stroke="${theme.border}"
      stroke-width="2"
    />
  `;

  svg += '</svg>';
  return svg;
}

// ═══════════════════════════════════════════════════════════════════════════
//  RADAR CHART RENDERER
// ═══════════════════════════════════════════════════════════════════════════

export function renderRadarChart(
  clusters: DataCluster[],
  config: GraphConfig,
  theme: Theme
): string {
  const centerX = config.width / 2;
  const centerY = config.height / 2;
  const radius = Math.min(
    config.width - config.padding.left - config.padding.right,
    config.height - config.padding.top - config.padding.bottom
  ) / 2 - 40;

  const numAxes = clusters.length;
  const angleStep = (2 * Math.PI) / numAxes;

  let svg = `
    <svg
      width="${config.width}"
      height="${config.height}"
      viewBox="0 0 ${config.width} ${config.height}"
      class="brutalist-chart radar-chart"
    >
      <rect width="100%" height="100%" fill="${theme.background}"/>
  `;

  // Grid circles
  if (config.showGrid) {
    for (let i = 1; i <= 5; i++) {
      const r = (radius / 5) * i;
      svg += `
        <circle
          cx="${centerX}"
          cy="${centerY}"
          r="${r}"
          fill="none"
          stroke="${theme.grid}"
          stroke-width="1"
        />
        <text
          x="${centerX + 5}"
          y="${centerY - r + 4}"
          fill="${theme.textMuted}"
          font-family="monospace"
          font-size="10"
        >${i * 20}%</text>
      `;
    }

    // Axis lines
    for (let i = 0; i < numAxes; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      svg += `
        <line
          x1="${centerX}"
          y1="${centerY}"
          x2="${x}"
          y2="${y}"
          stroke="${theme.grid}"
          stroke-width="1"
        />
      `;
    }
  }

  // Draw radar polygons for each series
  const numSeries = clusters[0]?.points.length || 0;

  for (let si = 0; si < numSeries; si++) {
    const color = theme.bars[si % theme.bars.length];
    let pathD = '';

    clusters.forEach((cluster, ci) => {
      const value = cluster.points[si]?.value || 0;
      const angle = ci * angleStep - Math.PI / 2;
      const r = (value / 100) * radius;
      const x = centerX + r * Math.cos(angle);
      const y = centerY + r * Math.sin(angle);
      pathD += ci === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
    });
    pathD += ' Z';

    svg += `
      <path
        d="${pathD}"
        fill="${color}"
        fill-opacity="0.1"
        stroke="${color}"
        stroke-width="2"
        class="radar-polygon"
        data-series="${si}"
      />
    `;

    // Points
    clusters.forEach((cluster, ci) => {
      const value = cluster.points[si]?.value || 0;
      const angle = ci * angleStep - Math.PI / 2;
      const r = (value / 100) * radius;
      const x = centerX + r * Math.cos(angle);
      const y = centerY + r * Math.sin(angle);
      svg += `
        <circle
          cx="${x}"
          cy="${y}"
          r="4"
          fill="${color}"
          stroke="${theme.background}"
          stroke-width="2"
          class="radar-point"
          data-cluster="${cluster.id}"
          data-point="${si}"
          data-value="${value}"
        />
      `;
    });
  }

  // Axis labels
  clusters.forEach((cluster, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const x = centerX + (radius + 30) * Math.cos(angle);
    const y = centerY + (radius + 30) * Math.sin(angle);
    svg += `
      <text
        x="${x}"
        y="${y}"
        text-anchor="middle"
        dominant-baseline="middle"
        fill="${theme.text}"
        font-family="monospace"
        font-size="9"
        font-weight="bold"
      >${cluster.name}</text>
    `;
  });

  svg += '</svg>';
  return svg;
}

// ═══════════════════════════════════════════════════════════════════════════
//  STACKED BAR CHART RENDERER
// ═══════════════════════════════════════════════════════════════════════════

export function renderStackedChart(
  clusters: DataCluster[],
  config: GraphConfig,
  theme: Theme
): string {
  const chartHeight = config.height - config.padding.top - config.padding.bottom;
  const chartWidth = config.width - config.padding.left - config.padding.right;
  const barWidth = (chartWidth / clusters.length) * 0.7;
  const barSpacing = (chartWidth / clusters.length) * 0.3;

  // Calculate max stacked value
  const maxStacked = Math.max(
    ...clusters.map((c) => c.points.reduce((sum, p) => sum + p.value, 0))
  );
  const yScale = (v: number) =>
    config.height - config.padding.bottom - (v / maxStacked) * chartHeight;

  let svg = `
    <svg
      width="${config.width}"
      height="${config.height}"
      viewBox="0 0 ${config.width} ${config.height}"
      class="brutalist-chart stacked-chart"
    >
      <rect width="100%" height="100%" fill="${theme.background}"/>
  `;

  // Grid
  if (config.showGrid) {
    for (let i = 0; i <= 5; i++) {
      const y = config.padding.top + (i / 5) * chartHeight;
      const value = Math.round(maxStacked - (i / 5) * maxStacked);
      svg += `
        <line
          x1="${config.padding.left}"
          y1="${y}"
          x2="${config.width - config.padding.right}"
          y2="${y}"
          stroke="${theme.grid}"
          stroke-width="1"
        />
        <text
          x="${config.padding.left - 10}"
          y="${y + 4}"
          text-anchor="end"
          fill="${theme.textMuted}"
          font-family="monospace"
          font-size="11"
        >${value}</text>
      `;
    }
  }

  // Stacked bars
  clusters.forEach((cluster, ci) => {
    const x = config.padding.left + ci * (barWidth + barSpacing) + barSpacing / 2;
    let currentY = config.height - config.padding.bottom;

    cluster.points.forEach((point, pi) => {
      const segmentHeight = (point.value / maxStacked) * chartHeight;
      const y = currentY - segmentHeight;
      const color = theme.bars[pi % theme.bars.length];

      svg += `
        <rect
          class="stacked-segment"
          data-cluster="${cluster.id}"
          data-point="${pi}"
          data-value="${point.value}"
          data-label="${point.label}"
          x="${x}"
          y="${y}"
          width="${barWidth}"
          height="${segmentHeight}"
          fill="${color}"
          stroke="${theme.border}"
          stroke-width="1"
        />
      `;

      currentY = y;
    });

    // Label
    svg += `
      <text
        x="${x + barWidth / 2}"
        y="${config.height - config.padding.bottom + 30}"
        text-anchor="middle"
        fill="${theme.text}"
        font-family="monospace"
        font-size="9"
        font-weight="bold"
      >${cluster.name}</text>
    `;
  });

  // Axes
  svg += `
    <line
      x1="${config.padding.left}"
      y1="${config.padding.top}"
      x2="${config.padding.left}"
      y2="${config.height - config.padding.bottom}"
      stroke="${theme.border}"
      stroke-width="2"
    />
    <line
      x1="${config.padding.left}"
      y1="${config.height - config.padding.bottom}"
      x2="${config.width - config.padding.right}"
      y2="${config.height - config.padding.bottom}"
      stroke="${theme.border}"
      stroke-width="2"
    />
  `;

  svg += '</svg>';
  return svg;
}

// ═══════════════════════════════════════════════════════════════════════════
//  MAIN RENDER FUNCTION - Dispatches to appropriate renderer
// ═══════════════════════════════════════════════════════════════════════════

export function renderGraph(
  clusters: DataCluster[],
  config: GraphConfig,
  theme: Theme
): string {
  const renderers: Record<GraphStyle, typeof renderBarChart> = {
    bar: renderBarChart,
    line: renderLineChart,
    radar: renderRadarChart,
    stacked: renderStackedChart,
  };

  const renderer = renderers[config.style] || renderBarChart;
  return renderer(clusters, config, theme);
}
