// JSON Design Generator - MVP
// Generates Figma designs from JSON data

// Show the UI panel
figma.showUI(__html__, { width: 400, height: 560 });

// Global font loading - call once at start of any generation
async function loadFonts() {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });
}

// Listen for messages from the UI
figma.ui.onmessage = async function(msg) {
  
  if (msg.type === 'generate') {
    try {
      var data = msg.data;
      var template = msg.template;
      var viewport = msg.viewport || 'desktop';
      
      // ALWAYS load fonts first before any generation
      await loadFonts();
      
      // Handle "both" viewport - generate desktop and mobile side by side
      if (viewport === 'both') {
        await generateBoth(data, template);
        figma.ui.postMessage({ type: 'success', message: 'Desktop + Mobile generated!' });
        return;
      }
      
      // Generate based on template type
      switch (template) {
        case 'cards':
          await generateCards(data, viewport);
          break;
        case 'list':
          await generateList(data, viewport);
          break;
        case 'table':
          await generateTable(data, viewport);
          break;
        case 'auto':
          await autoGenerate(data, viewport);
          break;
        default:
          await autoGenerate(data, viewport);
      }
      
      figma.ui.postMessage({ type: 'success', message: 'Design generated! (' + viewport + ')' });
      
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
  
  var arrayKeys = ['items', 'data', 'products', 'results', 'records', 'entries', 'rows', 'list'];
  
  for (var i = 0; i < arrayKeys.length; i++) {
    var key = arrayKeys[i];
    if (data[key] && Array.isArray(data[key])) {
      return data[key];
    }
  }
  
  for (var key in data) {
    if (Array.isArray(data[key]) && data[key].length > 0) {
      return data[key];
    }
  }
  
  return [data];
}

// ============================================
// HELPER: Create text node (font must be loaded first!)
// ============================================
function createText(content, options) {
  var text = figma.createText();
  text.fontName = options.fontName || { family: "Inter", style: "Regular" };
  text.characters = String(content);
  if (options.fontSize) text.fontSize = options.fontSize;
  if (options.fills) text.fills = options.fills;
  if (options.layoutAlign) text.layoutAlign = options.layoutAlign;
  return text;
}

// ============================================
// GENERATE BOTH: Desktop + Mobile side by side
// ============================================
async function generateBoth(data, template) {
  var items = extractItems(data);
  if (items.length === 0) {
    throw new Error('No data items found');
  }
  
  // Determine actual template if auto
  var actualTemplate = template;
  if (template === 'auto') {
    var firstItem = items[0];
    var keys = Object.keys(firstItem).filter(function(k) { return typeof firstItem[k] !== 'object'; });
    var keyCount = keys.length;
    var itemCount = items.length;
    
    if (keyCount <= 3 && itemCount > 5) {
      actualTemplate = 'list';
    } else if (keyCount >= 4 && itemCount >= 3) {
      actualTemplate = 'table';
    } else {
      actualTemplate = 'cards';
    }
  }
  
  // Create wrapper frame
  var wrapper = figma.createFrame();
  wrapper.name = "Responsive Design - Desktop & Mobile";
  wrapper.layoutMode = "HORIZONTAL";
  wrapper.itemSpacing = 60;
  wrapper.paddingLeft = 40;
  wrapper.paddingRight = 40;
  wrapper.paddingTop = 40;
  wrapper.paddingBottom = 40;
  wrapper.primaryAxisSizingMode = "AUTO";
  wrapper.counterAxisSizingMode = "AUTO";
  wrapper.fills = [{ type: 'SOLID', color: { r: 0.95, g: 0.95, b: 0.95 } }];
  wrapper.cornerRadius = 16;
  
  // Generate desktop version
  var desktopFrame;
  var mobileFrame;
  
  switch (actualTemplate) {
    case 'cards':
      desktopFrame = createCardsFrame(items, true);
      mobileFrame = createCardsFrame(items, false);
      break;
    case 'list':
      desktopFrame = createListFrame(items, true);
      mobileFrame = createListFrame(items, false);
      break;
    case 'table':
      desktopFrame = createTableFrame(items, true);
      mobileFrame = createTableFrame(items, false);
      break;
    default:
      desktopFrame = createCardsFrame(items, true);
      mobileFrame = createCardsFrame(items, false);
  }
  
  wrapper.appendChild(desktopFrame);
  wrapper.appendChild(mobileFrame);
  
  // Position and select
  wrapper.x = figma.viewport.center.x - wrapper.width / 2;
  wrapper.y = figma.viewport.center.y - wrapper.height / 2;
  figma.currentPage.selection = [wrapper];
  figma.viewport.scrollAndZoomIntoView([wrapper]);
}

// ============================================
// TEMPLATE: Cards Grid
// ============================================
async function generateCards(data, viewport) {
  var items = extractItems(data);
  var isDesktop = viewport !== 'mobile';
  
  var container = createCardsFrame(items, isDesktop);
  
  container.x = figma.viewport.center.x - container.width / 2;
  container.y = figma.viewport.center.y - container.height / 2;
  figma.currentPage.selection = [container];
  figma.viewport.scrollAndZoomIntoView([container]);
}

function createCardsFrame(items, isDesktop) {
  var containerWidth = isDesktop ? 1200 : 375;
  var cardWidth = isDesktop ? 280 : 335;
  var gap = isDesktop ? 24 : 16;
  var padding = isDesktop ? 32 : 20;
  
  var container = figma.createFrame();
  container.name = isDesktop ? "Cards - Desktop" : "Cards - Mobile";
  container.layoutMode = "HORIZONTAL";
  container.layoutWrap = "WRAP";
  container.itemSpacing = gap;
  container.counterAxisSpacing = gap;
  container.paddingLeft = padding;
  container.paddingRight = padding;
  container.paddingTop = padding;
  container.paddingBottom = padding;
  container.primaryAxisSizingMode = "FIXED";
  container.counterAxisSizingMode = "AUTO";
  container.resize(containerWidth, 100);
  container.fills = [{ type: 'SOLID', color: { r: 0.98, g: 0.98, b: 0.98 } }];
  container.cornerRadius = 12;
  
  for (var i = 0; i < items.length; i++) {
    var card = createCard(items[i], isDesktop, cardWidth);
    container.appendChild(card);
  }
  
  return container;
}

function createCard(item, isDesktop, cardWidth) {
  var card = figma.createFrame();
  card.name = item.title || item.name || "Card";
  card.layoutMode = "VERTICAL";
  card.itemSpacing = isDesktop ? 12 : 10;
  card.paddingLeft = isDesktop ? 20 : 16;
  card.paddingRight = isDesktop ? 20 : 16;
  card.paddingTop = isDesktop ? 20 : 16;
  card.paddingBottom = isDesktop ? 20 : 16;
  card.primaryAxisSizingMode = "AUTO";
  card.counterAxisSizingMode = "FIXED";
  card.resize(cardWidth, 100);
  card.cornerRadius = 12;
  card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
  card.effects = [{
    type: 'DROP_SHADOW',
    color: { r: 0, g: 0, b: 0, a: 0.1 },
    offset: { x: 0, y: 4 },
    radius: 12,
    spread: 0,
    visible: true,
    blendMode: 'NORMAL'
  }];
  
  var keys = Object.keys(item);
  
  for (var i = 0; i < keys.length; i++) {
    var key = keys[i];
    var value = item[key];
    if (value === null || value === undefined) continue;
    if (typeof value === 'object') continue;
    
    var keyLower = key.toLowerCase();
    var isTitle = keyLower === 'title' || keyLower === 'name' || keyLower === 'heading';
    var isPrice = keyLower === 'price' || keyLower === 'cost' || keyLower === 'amount';
    
    var text = createText(value, {
      fontName: isTitle ? { family: "Inter", style: "Semi Bold" } : { family: "Inter", style: "Regular" },
      fontSize: isTitle ? (isDesktop ? 18 : 16) : isPrice ? (isDesktop ? 16 : 15) : (isDesktop ? 14 : 13),
      fills: [{ 
        type: 'SOLID', 
        color: isPrice 
          ? { r: 0.2, g: 0.6, b: 0.4 } 
          : isTitle 
            ? { r: 0.1, g: 0.1, b: 0.1 }
            : { r: 0.4, g: 0.4, b: 0.4 }
      }],
      layoutAlign: "STRETCH"
    });
    
    card.appendChild(text);
  }
  
  return card;
}

// ============================================
// TEMPLATE: List
// ============================================
async function generateList(data, viewport) {
  var items = extractItems(data);
  var isDesktop = viewport !== 'mobile';
  
  var container = createListFrame(items, isDesktop);
  
  container.x = figma.viewport.center.x - container.width / 2;
  container.y = figma.viewport.center.y - container.height / 2;
  figma.currentPage.selection = [container];
  figma.viewport.scrollAndZoomIntoView([container]);
}

function createListFrame(items, isDesktop) {
  var containerWidth = isDesktop ? 500 : 375;
  
  var container = figma.createFrame();
  container.name = isDesktop ? "List - Desktop" : "List - Mobile";
  container.layoutMode = "VERTICAL";
  container.itemSpacing = 0;
  container.primaryAxisSizingMode = "AUTO";
  container.counterAxisSizingMode = "FIXED";
  container.resize(containerWidth, 100);
  container.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
  container.cornerRadius = 8;
  container.clipsContent = true;
  container.effects = [{
    type: 'DROP_SHADOW',
    color: { r: 0, g: 0, b: 0, a: 0.08 },
    offset: { x: 0, y: 2 },
    radius: 8,
    spread: 0,
    visible: true,
    blendMode: 'NORMAL'
  }];
  
  for (var i = 0; i < items.length; i++) {
    var row = createListRow(items[i], i === items.length - 1, isDesktop);
    container.appendChild(row);
  }
  
  return container;
}

function createListRow(item, isLast, isDesktop) {
  var row = figma.createFrame();
  row.name = item.title || item.name || "Row";
  row.layoutMode = "HORIZONTAL";
  row.itemSpacing = 12;
  row.paddingLeft = isDesktop ? 16 : 12;
  row.paddingRight = isDesktop ? 16 : 12;
  row.paddingTop = isDesktop ? 14 : 12;
  row.paddingBottom = isDesktop ? 14 : 12;
  row.primaryAxisSizingMode = "FIXED";
  row.counterAxisSizingMode = "AUTO";
  row.layoutAlign = "STRETCH";
  row.primaryAxisAlignItems = "SPACE_BETWEEN";
  row.counterAxisAlignItems = "CENTER";
  row.fills = [];
  
  if (!isLast) {
    row.strokes = [{ type: 'SOLID', color: { r: 0.9, g: 0.9, b: 0.9 } }];
    row.strokeWeight = 1;
    row.strokeAlign = "INSIDE";
    row.strokeTopWeight = 0;
    row.strokeLeftWeight = 0;
    row.strokeRightWeight = 0;
    row.strokeBottomWeight = 1;
  }
  
  var leftContent = figma.createFrame();
  leftContent.name = "Content";
  leftContent.layoutMode = "VERTICAL";
  leftContent.itemSpacing = 4;
  leftContent.primaryAxisSizingMode = "AUTO";
  leftContent.counterAxisSizingMode = "AUTO";
  leftContent.fills = [];
  leftContent.layoutGrow = 1;
  
  var keys = Object.keys(item).filter(function(k) { return typeof item[k] !== 'object'; });
  var primary = item.title || item.name || item[keys[0]];
  var secondary = item.description || item.subtitle || item[keys[1]];
  var rightValue = item.price || item.value || item.amount || item.status;
  
  if (primary) {
    var title = createText(primary, {
      fontName: { family: "Inter", style: "Semi Bold" },
      fontSize: isDesktop ? 14 : 13,
      fills: [{ type: 'SOLID', color: { r: 0.1, g: 0.1, b: 0.1 } }]
    });
    leftContent.appendChild(title);
  }
  
  if (secondary) {
    var subtitle = createText(secondary, {
      fontName: { family: "Inter", style: "Regular" },
      fontSize: isDesktop ? 12 : 11,
      fills: [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }]
    });
    leftContent.appendChild(subtitle);
  }
  
  row.appendChild(leftContent);
  
  if (rightValue) {
    var value = createText(rightValue, {
      fontName: { family: "Inter", style: "Semi Bold" },
      fontSize: isDesktop ? 14 : 13,
      fills: [{ type: 'SOLID', color: { r: 0.2, g: 0.6, b: 0.4 } }]
    });
    row.appendChild(value);
  }
  
  return row;
}

// ============================================
// TEMPLATE: Table
// ============================================
async function generateTable(data, viewport) {
  var items = extractItems(data);
  if (items.length === 0) return;
  
  var isDesktop = viewport !== 'mobile';
  
  var container = createTableFrame(items, isDesktop);
  
  container.x = figma.viewport.center.x - container.width / 2;
  container.y = figma.viewport.center.y - container.height / 2;
  figma.currentPage.selection = [container];
  figma.viewport.scrollAndZoomIntoView([container]);
}

function createTableFrame(items, isDesktop) {
  var columns = Object.keys(items[0]).filter(function(k) { return typeof items[0][k] !== 'object'; });
  
  // For mobile, only show first 2 columns to avoid truncation
  if (!isDesktop && columns.length > 2) {
    columns = columns.slice(0, 2);
  }
  
  // Calculate column width based on number of columns
  var totalWidth = isDesktop ? 900 : 340;
  var colWidth = Math.floor(totalWidth / columns.length);
  
  var container = figma.createFrame();
  container.name = isDesktop ? "Table - Desktop" : "Table - Mobile";
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
    container.appendChild(row);
  }
  
  return container;
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
    
    // Get cell value - ensure it's never empty
    var cellValue = values[i];
    var displayValue = (cellValue !== null && cellValue !== undefined && cellValue !== '') 
      ? String(cellValue) 
      : '-';
    
    // Create text node
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
    
    // Add to cell FIRST, then set layout properties
    cell.appendChild(text);
    text.textTruncation = "ENDING";
    text.layoutSizingHorizontal = "FILL";
    
    row.appendChild(cell);
  }
  
  return row;
}

// ============================================
// AUTO-DETECT: Smart template selection
// ============================================
async function autoGenerate(data, viewport) {
  var items = extractItems(data);
  
  if (items.length === 0) {
    throw new Error('No data items found');
  }
  
  var firstItem = items[0];
  var keys = Object.keys(firstItem).filter(function(k) { return typeof firstItem[k] !== 'object'; });
  var keyCount = keys.length;
  var itemCount = items.length;
  
  if (keyCount <= 3 && itemCount > 5) {
    await generateList(data, viewport);
  } else if (keyCount >= 4 && itemCount >= 3) {
    await generateTable(data, viewport);
  } else {
    await generateCards(data, viewport);
  }
}
