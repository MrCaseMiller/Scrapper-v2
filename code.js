// Dynamic Table Generator - Figma Plugin
// Generates tables that adapt to any JSON data structure

figma.showUI(__html__, { width: 420, height: 520 });

// Load fonts once at startup
async function loadFonts() {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });
}

// Listen for messages from UI
figma.ui.onmessage = async function(msg) {
  if (msg.type === 'generate') {
    try {
      await loadFonts();

      var data = msg.data;
      var options = msg.options || {};

      // Extract array from data
      var items = extractItems(data);
      if (items.length === 0) {
        throw new Error('No data items found');
      }

      // Generate table
      var table = createDynamicTable(items, options);

      // Position in viewport
      table.x = figma.viewport.center.x - table.width / 2;
      table.y = figma.viewport.center.y - table.height / 2;

      figma.currentPage.selection = [table];
      figma.viewport.scrollAndZoomIntoView([table]);

      figma.ui.postMessage({ type: 'success', message: 'Table generated!' });

    } catch (error) {
      figma.ui.postMessage({ type: 'error', message: error.message });
    }
  }

  if (msg.type === 'cancel') {
    figma.closePlugin();
  }
};

// ============================================
// HELPER: Extract array from various JSON structures
// ============================================
function extractItems(data) {
  if (Array.isArray(data)) return data;

  // Common array key names
  var arrayKeys = ['items', 'data', 'products', 'results', 'records',
                   'entries', 'rows', 'list', 'competitors', 'users'];

  for (var i = 0; i < arrayKeys.length; i++) {
    var key = arrayKeys[i];
    if (data[key] && Array.isArray(data[key])) {
      return data[key];
    }
  }

  // Find first array in data
  for (var key in data) {
    if (Array.isArray(data[key]) && data[key].length > 0) {
      return data[key];
    }
  }

  return [data];
}

// ============================================
// HELPER: Flatten nested object with dot notation
// ============================================
function flattenObject(obj, prefix, maxDepth, currentDepth) {
  prefix = prefix || '';
  maxDepth = maxDepth || 2;
  currentDepth = currentDepth || 0;

  var result = {};

  for (var key in obj) {
    var value = obj[key];
    var newKey = prefix ? prefix + '.' + key : key;

    if (value === null || value === undefined) {
      result[newKey] = '-';
    } else if (Array.isArray(value)) {
      // Join arrays as comma-separated string
      result[newKey] = value.join(', ');
    } else if (typeof value === 'object' && currentDepth < maxDepth) {
      // Recursively flatten nested objects
      var nested = flattenObject(value, newKey, maxDepth, currentDepth + 1);
      for (var nestedKey in nested) {
        result[nestedKey] = nested[nestedKey];
      }
    } else if (typeof value === 'object') {
      // Max depth reached, stringify
      result[newKey] = JSON.stringify(value);
    } else {
      result[newKey] = value;
    }
  }

  return result;
}

// ============================================
// HELPER: Format column header from key
// ============================================
function formatHeader(key) {
  // Remove dot notation prefixes for cleaner headers
  var parts = key.split('.');
  var lastPart = parts[parts.length - 1];

  // Convert camelCase/snake_case to Title Case
  return lastPart
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, function(c) { return c.toUpperCase(); });
}

// ============================================
// HELPER: Measure text width approximation
// ============================================
function estimateTextWidth(text, fontSize) {
  // Approximate character width (Inter font)
  var avgCharWidth = fontSize * 0.5;
  return String(text).length * avgCharWidth;
}

// ============================================
// MAIN: Create Dynamic Table
// ============================================
function createDynamicTable(items, options) {
  var flatten = options.flatten !== false;
  var maxDepth = options.maxDepth || 2;
  var selectedColumns = options.columns || null;
  var maxWidth = options.maxWidth || 1600;
  var minColWidth = options.minColWidth || 120;
  var maxColWidth = options.maxColWidth || 280;
  var tableName = options.tableName || 'Dynamic Table';

  // Flatten items if needed
  var flatItems = items.map(function(item) {
    return flatten ? flattenObject(item, '', maxDepth, 0) : item;
  });

  // Get all unique columns
  var allColumns = [];
  var columnSet = {};
  flatItems.forEach(function(item) {
    Object.keys(item).forEach(function(key) {
      if (!columnSet[key] && typeof item[key] !== 'object') {
        columnSet[key] = true;
        allColumns.push(key);
      }
    });
  });

  // Filter to selected columns if specified
  var columns = selectedColumns ?
    allColumns.filter(function(c) { return selectedColumns.indexOf(c) >= 0; }) :
    allColumns;

  // Limit columns to fit maxWidth reasonably
  var maxCols = Math.floor(maxWidth / minColWidth);
  if (columns.length > maxCols) {
    columns = columns.slice(0, maxCols);
  }

  // Calculate column widths based on content
  var colWidths = columns.map(function(col) {
    // Start with header width
    var headerWidth = estimateTextWidth(formatHeader(col), 13) + 24;
    var maxContentWidth = headerWidth;

    // Check content widths
    flatItems.forEach(function(item) {
      var value = item[col];
      if (value !== null && value !== undefined) {
        var contentWidth = estimateTextWidth(String(value), 13) + 24;
        maxContentWidth = Math.max(maxContentWidth, contentWidth);
      }
    });

    // Clamp to min/max
    return Math.max(minColWidth, Math.min(maxColWidth, maxContentWidth));
  });

  // Distribute remaining width proportionally if under maxWidth
  var totalWidth = colWidths.reduce(function(a, b) { return a + b; }, 0);
  if (totalWidth < maxWidth && columns.length > 0) {
    var extraPerCol = Math.min(50, (maxWidth - totalWidth) / columns.length);
    colWidths = colWidths.map(function(w) { return w + extraPerCol; });
  }

  // Create main container
  var container = figma.createFrame();
  container.name = tableName;
  container.layoutMode = "VERTICAL";
  container.itemSpacing = 0;
  container.primaryAxisSizingMode = "AUTO";
  container.counterAxisSizingMode = "AUTO";
  container.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
  container.cornerRadius = 8;
  container.clipsContent = true;
  container.effects = [{
    type: 'DROP_SHADOW',
    color: { r: 0, g: 0, b: 0, a: 0.08 },
    offset: { x: 0, y: 2 },
    radius: 12,
    spread: 0,
    visible: true,
    blendMode: 'NORMAL'
  }];

  // Create header row
  var headerRow = createTableRow(columns, columns.map(formatHeader), colWidths, true, false);
  container.appendChild(headerRow);

  // Create data rows
  for (var i = 0; i < flatItems.length; i++) {
    var item = flatItems[i];
    var values = columns.map(function(col) {
      var val = item[col];
      if (val === null || val === undefined || val === '') return '-';
      return String(val);
    });
    var isLast = i === flatItems.length - 1;
    var row = createTableRow(columns, values, colWidths, false, isLast);
    container.appendChild(row);
  }

  return container;
}

// ============================================
// HELPER: Create Table Row
// ============================================
function createTableRow(columns, values, colWidths, isHeader, isLast) {
  var row = figma.createFrame();
  row.name = isHeader ? "Header" : "Row";
  row.layoutMode = "HORIZONTAL";
  row.itemSpacing = 0;
  row.primaryAxisSizingMode = "AUTO";
  row.counterAxisSizingMode = "AUTO";
  row.counterAxisAlignItems = "MIN";
  row.fills = isHeader
    ? [{ type: 'SOLID', color: { r: 0.97, g: 0.97, b: 0.97 } }]
    : [];

  // Add bottom border for non-last rows
  if (!isLast) {
    row.strokes = [{ type: 'SOLID', color: { r: 0.92, g: 0.92, b: 0.92 } }];
    row.strokeWeight = 1;
    row.strokeAlign = "INSIDE";
    row.strokeTopWeight = 0;
    row.strokeLeftWeight = 0;
    row.strokeRightWeight = 0;
    row.strokeBottomWeight = 1;
  }

  for (var i = 0; i < columns.length; i++) {
    var cell = createTableCell(columns[i], values[i], colWidths[i], isHeader, i === 0);
    row.appendChild(cell);
  }

  return row;
}

// ============================================
// HELPER: Create Table Cell with Text Wrap
// ============================================
function createTableCell(columnName, value, width, isHeader, isFirst) {
  var cell = figma.createFrame();
  cell.name = columnName;
  cell.layoutMode = "VERTICAL";
  cell.primaryAxisSizingMode = "AUTO";
  cell.counterAxisSizingMode = "FIXED";
  cell.layoutAlign = "STRETCH";
  cell.resize(width, 40);
  cell.paddingLeft = 12;
  cell.paddingRight = 12;
  cell.paddingTop = 12;
  cell.paddingBottom = 12;
  cell.fills = [];
  cell.clipsContent = false;

  // Add left border for non-first cells
  if (!isFirst) {
    cell.strokes = [{ type: 'SOLID', color: { r: 0.92, g: 0.92, b: 0.92 } }];
    cell.strokeWeight = 1;
    cell.strokeAlign = "INSIDE";
    cell.strokeTopWeight = 0;
    cell.strokeLeftWeight = 1;
    cell.strokeRightWeight = 0;
    cell.strokeBottomWeight = 0;
  }

  // Get display value - ensure it's never empty
  var displayValue = (value !== null && value !== undefined && value !== '')
    ? String(value)
    : '-';

  // Create text node
  var text = figma.createText();
  text.fontName = isHeader
    ? { family: "Inter", style: "Semi Bold" }
    : { family: "Inter", style: "Regular" };
  text.fontSize = 13;
  text.characters = displayValue;
  text.fills = [{
    type: 'SOLID',
    color: isHeader
      ? { r: 0.3, g: 0.3, b: 0.3 }
      : { r: 0.2, g: 0.2, b: 0.2 }
  }];

  // Add to cell FIRST, then set layout properties
  cell.appendChild(text);
  text.layoutSizingHorizontal = "FILL";
  text.textAutoResize = "HEIGHT";

  return cell;
}
