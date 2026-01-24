// Section to JSON Table
// Extracts a Figma section's contents to JSON, then lets user generate a table from it

figma.showUI(__html__, { width: 480, height: 620 });

// Check initial selection and notify UI
updateSelectionInfo();

// Listen for selection changes
figma.on('selectionchange', function() {
  updateSelectionInfo();
});

function updateSelectionInfo() {
  var selection = figma.currentPage.selection;
  if (selection.length === 1) {
    var node = selection[0];
    figma.ui.postMessage({
      type: 'selection-update',
      name: node.name,
      nodeType: node.type,
      valid: node.type === 'SECTION' || node.type === 'FRAME' || node.type === 'GROUP'
    });
  } else {
    figma.ui.postMessage({
      type: 'selection-update',
      name: null,
      nodeType: null,
      valid: false
    });
  }
}

// ============================================
// EXTRACTION: Recursive node traversal
// ============================================
function extractNode(node, options, depth) {
  if (depth > (options.maxDepth || 20)) return null;
  if (!node.visible && !options.includeHidden) return null;

  var result = {
    type: node.type,
    name: node.name
  };

  // Position and size
  if (options.includePosition) {
    result.x = Math.round(node.x);
    result.y = Math.round(node.y);
    result.width = Math.round(node.width);
    result.height = Math.round(node.height);
  }

  // Style properties
  if (options.includeStyles && 'fills' in node) {
    var style = extractStyles(node);
    if (Object.keys(style).length > 0) {
      result.style = style;
    }
  }

  // Layout properties (auto-layout frames)
  if ('layoutMode' in node && node.layoutMode !== 'NONE') {
    result.layout = {
      mode: node.layoutMode,
      itemSpacing: node.itemSpacing,
      paddingTop: node.paddingTop,
      paddingRight: node.paddingRight,
      paddingBottom: node.paddingBottom,
      paddingLeft: node.paddingLeft,
      primaryAxisAlignItems: node.primaryAxisAlignItems,
      counterAxisAlignItems: node.counterAxisAlignItems
    };
  }

  // Text properties
  if (node.type === 'TEXT') {
    result.characters = node.characters;
    if (options.includeTextStyles) {
      if (node.fontSize !== figma.mixed) {
        result.fontSize = node.fontSize;
      }
      if (node.fontName !== figma.mixed) {
        result.fontFamily = node.fontName.family;
        result.fontStyle = node.fontName.style;
      }
      result.textAlignHorizontal = node.textAlignHorizontal;
    }
  }

  // Instance reference
  if (node.type === 'INSTANCE' && node.mainComponent) {
    result.componentName = node.mainComponent.name;
  }

  // Recurse into children
  if ('children' in node && node.children.length > 0) {
    result.children = [];
    for (var i = 0; i < node.children.length; i++) {
      var child = extractNode(node.children[i], options, depth + 1);
      if (child) {
        result.children.push(child);
      }
    }
    if (result.children.length === 0) delete result.children;
  }

  return result;
}

function extractStyles(node) {
  var style = {};

  // Fills
  if (node.fills && node.fills !== figma.mixed && node.fills.length > 0) {
    var visibleFills = node.fills.filter(function(f) { return f.visible !== false; });
    if (visibleFills.length > 0) {
      style.fills = visibleFills.map(function(fill) {
        if (fill.type === 'SOLID') {
          return { type: 'SOLID', color: rgbToHex(fill.color), opacity: fill.opacity };
        }
        return { type: fill.type };
      });
    }
  }

  // Strokes
  if (node.strokes && node.strokes.length > 0) {
    var visibleStrokes = node.strokes.filter(function(s) { return s.visible !== false; });
    if (visibleStrokes.length > 0) {
      style.strokes = visibleStrokes.map(function(stroke) {
        if (stroke.type === 'SOLID') {
          return { type: 'SOLID', color: rgbToHex(stroke.color) };
        }
        return { type: stroke.type };
      });
      style.strokeWeight = node.strokeWeight;
    }
  }

  // Corner radius
  if ('cornerRadius' in node && node.cornerRadius && node.cornerRadius !== 0 && node.cornerRadius !== figma.mixed) {
    style.cornerRadius = node.cornerRadius;
  }

  // Effects
  if (node.effects && node.effects.length > 0) {
    var visibleEffects = node.effects.filter(function(e) { return e.visible; });
    if (visibleEffects.length > 0) {
      style.effects = visibleEffects.map(function(effect) {
        var e = { type: effect.type };
        if (effect.radius !== undefined) e.radius = effect.radius;
        return e;
      });
    }
  }

  // Opacity
  if (node.opacity !== undefined && node.opacity !== 1) {
    style.opacity = node.opacity;
  }

  return style;
}

// ============================================
// FLATTEN: Convert tree to tabular rows
// ============================================
function flattenToRows(node, rows, depth) {
  if (!node) return;

  var row = {
    name: node.name,
    type: node.type,
    depth: depth
  };

  if (node.width !== undefined) row.width = node.width;
  if (node.height !== undefined) row.height = node.height;
  if (node.characters) row.text = node.characters;
  if (node.fontSize) row.fontSize = node.fontSize;
  if (node.fontFamily) row.fontFamily = node.fontFamily;
  if (node.layout) row.layout = node.layout.mode;
  if (node.style && node.style.fills && node.style.fills[0]) {
    row.fill = node.style.fills[0].color || '';
  }
  if (node.componentName) row.component = node.componentName;

  rows.push(row);

  if (node.children) {
    for (var i = 0; i < node.children.length; i++) {
      flattenToRows(node.children[i], rows, depth + 1);
    }
  }
}

// ============================================
// TABLE GENERATION (from flattened JSON data)
// ============================================
async function generateTable(items, viewport) {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });

  if (items.length === 0) {
    figma.ui.postMessage({ type: 'error', message: 'No items to generate table from.' });
    return;
  }

  var isDesktop = viewport !== 'mobile';

  // Determine columns from the first item's keys (exclude 'depth' for cleaner output)
  var columns = Object.keys(items[0]).filter(function(k) {
    return k !== 'depth';
  });

  // For mobile, limit columns
  if (!isDesktop && columns.length > 3) {
    columns = columns.slice(0, 3);
  }

  var totalWidth = isDesktop ? 960 : 375;
  var colWidth = Math.floor(totalWidth / columns.length);

  var container = figma.createFrame();
  container.name = "Section JSON Table - " + (isDesktop ? "Desktop" : "Mobile");
  container.layoutMode = "VERTICAL";
  container.itemSpacing = 0;
  container.primaryAxisSizingMode = "AUTO";
  container.counterAxisSizingMode = "AUTO";
  container.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
  container.cornerRadius = 8;
  container.clipsContent = false;
  container.effects = [{
    type: 'DROP_SHADOW',
    color: { r: 0, g: 0, b: 0, a: 0.08 },
    offset: { x: 0, y: 2 },
    radius: 8,
    spread: 0,
    visible: true,
    blendMode: 'NORMAL'
  }];

  // Header row
  var header = createTableRow(columns, columns, true, false, isDesktop, colWidth);
  container.appendChild(header);

  // Data rows
  for (var i = 0; i < items.length; i++) {
    var rowData = columns.map(function(col) { return items[i][col]; });
    var row = createTableRow(columns, rowData, false, i === items.length - 1, isDesktop, colWidth);

    // Indent based on depth for visual hierarchy
    if (items[i].depth !== undefined && items[i].depth > 0) {
      row.fills = [{ type: 'SOLID', color: { r: 0.99, g: 0.99, b: 0.99 } }];
    }

    container.appendChild(row);
  }

  // Position and select
  container.x = figma.viewport.center.x - container.width / 2;
  container.y = figma.viewport.center.y - container.height / 2;
  figma.currentPage.selection = [container];
  figma.viewport.scrollAndZoomIntoView([container]);

  figma.ui.postMessage({ type: 'success', message: 'Table created with ' + items.length + ' rows!' });
}

function createTableRow(columns, values, isHeader, isLast, isDesktop, colWidth) {
  var row = figma.createFrame();
  row.name = isHeader ? "Header" : "Row";
  row.layoutMode = "HORIZONTAL";
  row.itemSpacing = 0;
  row.primaryAxisSizingMode = "AUTO";
  row.counterAxisSizingMode = "AUTO";
  row.fills = isHeader
    ? [{ type: 'SOLID', color: { r: 0.96, g: 0.96, b: 0.96 } }]
    : [];

  if (!isHeader && !isLast) {
    row.strokes = [{ type: 'SOLID', color: { r: 0.92, g: 0.92, b: 0.92 } }];
    row.strokeWeight = 1;
    row.strokeAlign = "INSIDE";
    row.strokeTopWeight = 0;
    row.strokeLeftWeight = 0;
    row.strokeRightWeight = 0;
    row.strokeBottomWeight = 1;
  }

  for (var i = 0; i < columns.length; i++) {
    var cell = figma.createFrame();
    cell.name = columns[i];
    cell.layoutMode = "HORIZONTAL";
    cell.counterAxisAlignItems = "CENTER";
    cell.primaryAxisSizingMode = "FIXED";
    cell.counterAxisSizingMode = "AUTO";
    cell.resize(colWidth, 40);
    cell.paddingLeft = isDesktop ? 12 : 8;
    cell.paddingRight = isDesktop ? 12 : 8;
    cell.paddingTop = isDesktop ? 12 : 10;
    cell.paddingBottom = isDesktop ? 12 : 10;
    cell.fills = [];
    cell.clipsContent = true;

    var cellValue = values[i];
    var displayValue = (cellValue !== null && cellValue !== undefined && cellValue !== '')
      ? String(cellValue)
      : '-';

    var text = figma.createText();
    text.fontName = isHeader
      ? { family: "Inter", style: "Semi Bold" }
      : { family: "Inter", style: "Regular" };
    text.fontSize = isDesktop ? 13 : 11;
    text.characters = displayValue;
    text.fills = [{
      type: 'SOLID',
      color: isHeader
        ? { r: 0.3, g: 0.3, b: 0.3 }
        : { r: 0.2, g: 0.2, b: 0.2 }
    }];

    cell.appendChild(text);
    text.textTruncation = "ENDING";
    text.layoutSizingHorizontal = "FILL";

    row.appendChild(cell);
  }

  return row;
}

// ============================================
// UTILITIES
// ============================================
function rgbToHex(color) {
  var r = Math.round(color.r * 255);
  var g = Math.round(color.g * 255);
  var b = Math.round(color.b * 255);
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

// ============================================
// MESSAGE HANDLER
// ============================================
figma.ui.onmessage = async function(msg) {

  if (msg.type === 'extract-section') {
    var selection = figma.currentPage.selection;

    if (selection.length === 0) {
      figma.ui.postMessage({ type: 'error', message: 'Please select a Section, Frame, or Group on the canvas.' });
      return;
    }

    var target = selection[0];

    if (target.type !== 'SECTION' && target.type !== 'FRAME' && target.type !== 'GROUP') {
      figma.ui.postMessage({
        type: 'error',
        message: 'Selected node is "' + target.type + '". Please select a SECTION, FRAME, or GROUP.'
      });
      return;
    }

    var options = msg.options || {
      includePosition: true,
      includeStyles: true,
      includeTextStyles: true,
      includeHidden: false,
      maxDepth: 20
    };

    // Perform extraction
    var result = extractNode(target, options, 0);

    // Count nodes
    var nodeCount = 0;
    function countNodes(n) {
      nodeCount++;
      if (n.children) {
        for (var i = 0; i < n.children.length; i++) {
          countNodes(n.children[i]);
        }
      }
    }
    countNodes(result);

    // Flatten to rows for table generation
    var rows = [];
    flattenToRows(result, rows, 0);

    var output = {
      section: result,
      metadata: {
        extractedAt: new Date().toISOString(),
        nodeCount: nodeCount,
        sourceFile: figma.root.name,
        sourcePage: figma.currentPage.name
      }
    };

    figma.ui.postMessage({
      type: 'extraction-result',
      json: JSON.stringify(output, null, 2),
      nodeCount: nodeCount,
      rows: rows
    });
  }

  if (msg.type === 'create-table') {
    try {
      var items = msg.rows;
      var viewport = msg.viewport || 'desktop';
      await generateTable(items, viewport);
    } catch (error) {
      figma.ui.postMessage({ type: 'error', message: error.message });
    }
  }

  if (msg.type === 'cancel') {
    figma.closePlugin();
  }
};
