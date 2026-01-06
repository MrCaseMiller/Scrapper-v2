// Graph renderers
function renderBarChart(clusters, isDark) {
  const { width, height, padding } = CONFIG;
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;
  const maxVal = Math.ceil(Math.max(...clusters.flatMap(c => c.points.map(p => p.value))) / 10) * 10;
  const clusterW = chartW / clusters.length;
  const maxBars = Math.max(...clusters.map(c => c.points.length));
  const barW = Math.max(10, (clusterW - 20) / maxBars - 4);

  let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;
  svg += `<rect width="100%" height="100%" fill="${isDark ? '#1a1a1a' : '#f5f5f5'}"/>`;

  for (let i = 0; i <= 10; i++) {
    const y = padding.top + (i / 10) * chartH;
    const val = maxVal - (i / 10) * maxVal;
    svg += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="${isDark ? '#333' : '#e0e0e0'}" stroke-width="0.5"/>`;
    svg += `<text x="${padding.left - 10}" y="${y + 4}" text-anchor="end" fill="${isDark ? '#666' : '#999'}" font-family="monospace" font-size="9">${val}%</text>`;
  }

  clusters.forEach((cluster, ci) => {
    const cx = padding.left + (ci + 0.5) * clusterW;
    const startX = cx - (cluster.points.length * (barW + 2)) / 2;

    cluster.points.forEach((pt, pi) => {
      const barH = (pt.value / maxVal) * chartH;
      const x = startX + pi * (barW + 2);
      const y = height - padding.bottom - barH;
      svg += `<rect class="bar" data-cluster="${cluster.id}" data-idx="${pi}" x="${x}" y="${y}" width="${barW}" height="${barH}" fill="${COLORS[pi % COLORS.length]}"/>`;
    });

    svg += `<text x="${cx}" y="${height - padding.bottom + 35}" text-anchor="middle" fill="${isDark ? '#888' : '#666'}" font-family="monospace" font-size="9">${cluster.name}</text>`;
  });

  svg += `<line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" stroke="${isDark ? '#444' : '#ccc'}" stroke-width="0.5"/>`;
  svg += `<line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" stroke="${isDark ? '#444' : '#ccc'}" stroke-width="0.5"/>`;
  svg += '</svg>';
  return svg;
}

function renderLineChart(clusters, isDark) {
  const { width, height, padding } = CONFIG;
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;
  const maxVal = Math.ceil(Math.max(...clusters.flatMap(c => c.points.map(p => p.value))) / 10) * 10;
  const pointSpacing = chartW / (clusters.length - 1 || 1);
  const numSeries = clusters[0]?.points.length || 0;

  let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;
  svg += `<rect width="100%" height="100%" fill="${isDark ? '#1a1a1a' : '#f5f5f5'}"/>`;

  for (let i = 0; i <= 10; i++) {
    const y = padding.top + (i / 10) * chartH;
    svg += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="${isDark ? '#333' : '#e0e0e0'}" stroke-width="0.5"/>`;
  }

  for (let si = 0; si < numSeries; si++) {
    let path = '';
    clusters.forEach((c, ci) => {
      const x = padding.left + ci * pointSpacing;
      const y = height - padding.bottom - (c.points[si].value / maxVal) * chartH;
      path += ci === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
    });
    svg += `<path d="${path}" fill="none" stroke="${COLORS[si % COLORS.length]}" stroke-width="1.5"/>`;

    clusters.forEach((c, ci) => {
      const x = padding.left + ci * pointSpacing;
      const y = height - padding.bottom - (c.points[si].value / maxVal) * chartH;
      svg += `<circle class="bar" data-cluster="${c.id}" data-idx="${si}" cx="${x}" cy="${y}" r="4" fill="${COLORS[si % COLORS.length]}"/>`;
    });
  }

  clusters.forEach((c, i) => {
    const x = padding.left + i * pointSpacing;
    svg += `<text x="${x}" y="${height - padding.bottom + 25}" text-anchor="middle" fill="${isDark ? '#888' : '#666'}" font-family="monospace" font-size="9">${c.name}</text>`;
  });

  svg += '</svg>';
  return svg;
}

function renderRadarChart(clusters, isDark) {
  const { width, height } = CONFIG;
  const cx = width / 2, cy = height / 2;
  const radius = Math.min(width, height) / 2 - 80;
  const numAxes = clusters.length;
  const angleStep = (2 * Math.PI) / numAxes;
  const numSeries = clusters[0]?.points.length || 0;

  let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;
  svg += `<rect width="100%" height="100%" fill="${isDark ? '#1a1a1a' : '#f5f5f5'}"/>`;

  for (let i = 1; i <= 5; i++) {
    const r = (radius / 5) * i;
    svg += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${isDark ? '#333' : '#e0e0e0'}" stroke-width="0.5"/>`;
  }

  for (let i = 0; i < numAxes; i++) {
    const angle = i * angleStep - Math.PI / 2;
    const x = cx + radius * Math.cos(angle);
    const y = cy + radius * Math.sin(angle);
    svg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="${isDark ? '#333' : '#e0e0e0'}" stroke-width="0.5"/>`;
  }

  for (let si = 0; si < numSeries; si++) {
    let path = '';
    clusters.forEach((c, ci) => {
      const val = c.points[si].value;
      const angle = ci * angleStep - Math.PI / 2;
      const r = (val / 100) * radius;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      path += ci === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
    });
    path += ' Z';
    svg += `<path d="${path}" fill="${COLORS[si % COLORS.length]}" fill-opacity="0.12" stroke="${COLORS[si % COLORS.length]}" stroke-width="1"/>`;
  }

  clusters.forEach((c, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const x = cx + (radius + 30) * Math.cos(angle);
    const y = cy + (radius + 30) * Math.sin(angle);
    svg += `<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="middle" fill="${isDark ? '#888' : '#666'}" font-family="monospace" font-size="9">${c.name}</text>`;
  });

  svg += '</svg>';
  return svg;
}

function renderStackedChart(clusters, isDark) {
  const { width, height, padding } = CONFIG;
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;
  const maxStacked = Math.max(...clusters.map(c => c.points.reduce((s, p) => s + p.value, 0)));
  const barW = (chartW / clusters.length) * 0.7;
  const barSpacing = (chartW / clusters.length) * 0.3;

  let svg = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;
  svg += `<rect width="100%" height="100%" fill="${isDark ? '#1a1a1a' : '#f5f5f5'}"/>`;

  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (i / 5) * chartH;
    svg += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="${isDark ? '#333' : '#e0e0e0'}" stroke-width="0.5"/>`;
  }

  clusters.forEach((c, ci) => {
    const x = padding.left + ci * (barW + barSpacing) + barSpacing / 2;
    let curY = height - padding.bottom;

    c.points.forEach((pt, pi) => {
      const segH = (pt.value / maxStacked) * chartH;
      const y = curY - segH;
      svg += `<rect class="bar" data-cluster="${c.id}" data-idx="${pi}" x="${x}" y="${y}" width="${barW}" height="${segH}" fill="${COLORS[pi % COLORS.length]}"/>`;
      curY = y;
    });

    svg += `<text x="${x + barW / 2}" y="${height - padding.bottom + 25}" text-anchor="middle" fill="${isDark ? '#888' : '#666'}" font-family="monospace" font-size="9">${c.name}</text>`;
  });

  svg += '</svg>';
  return svg;
}

const RENDERERS = { bar: renderBarChart, line: renderLineChart, radar: renderRadarChart, stacked: renderStackedChart };
