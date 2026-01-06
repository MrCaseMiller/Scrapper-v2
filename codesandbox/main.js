// Main application logic
let currentDataset = 'ablation';
let currentStyle = 'bar';
let isDark = false;

function render() {
  const data = DATASETS[currentDataset];
  document.getElementById('graphTitle').textContent = data.title;
  document.getElementById('graphBody').innerHTML = RENDERERS[currentStyle](data.clusters, isDark);

  document.getElementById('legend').innerHTML = data.clusters[0].points.map((pt, i) =>
    `<div class="legend-item"><div class="legend-swatch" style="background:${COLORS[i % COLORS.length]}"></div><span>${pt.label}</span></div>`
  ).join('');

  document.querySelectorAll('.bar').forEach(bar => {
    bar.addEventListener('mouseenter', showTooltip);
    bar.addEventListener('mousemove', moveTooltip);
    bar.addEventListener('mouseleave', hideTooltip);
  });
}

function showTooltip(e) {
  const clusterId = e.target.getAttribute('data-cluster');
  const cluster = DATASETS[currentDataset].clusters.find(c => c.id === clusterId);
  if (!cluster) return;

  document.getElementById('tooltipHeader').textContent = cluster.name;
  document.getElementById('tooltipBody').innerHTML = cluster.points.map((pt, i) =>
    `<div class="tooltip-row"><span><div class="tooltip-swatch" style="background:${COLORS[i % COLORS.length]}"></div>${pt.label}</span><strong>${pt.value}%</strong></div>`
  ).join('');

  document.getElementById('tooltip').classList.add('visible');
}

function moveTooltip(e) {
  const tooltip = document.getElementById('tooltip');
  tooltip.style.left = (e.clientX + 15) + 'px';
  tooltip.style.top = (e.clientY - 10) + 'px';
}

function hideTooltip() {
  document.getElementById('tooltip').classList.remove('visible');
}

// Event listeners
document.getElementById('datasetSelect').addEventListener('change', e => {
  currentDataset = e.target.value;
  render();
});

document.getElementById('styleSelect').addEventListener('change', e => {
  currentStyle = e.target.value;
  render();
});

document.getElementById('themeToggle').addEventListener('click', () => {
  isDark = !isDark;
  document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');
  document.getElementById('themeToggle').textContent = isDark ? 'LIGHT' : 'DARK';
  render();
});

document.getElementById('exportSvg').addEventListener('click', () => {
  const svg = document.querySelector('#graphBody svg');
  if (!svg) return;
  const blob = new Blob([svg.outerHTML], { type: 'image/svg+xml' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${currentDataset}-${currentStyle}.svg`;
  a.click();
});

// Initialize
render();
