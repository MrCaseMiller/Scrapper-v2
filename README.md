# JSON Design Generator - Figma Plugin

A minimal Figma plugin that generates designs from JSON data. Paste JSON, pick a template, get a design.

## Quick Install (30 seconds)

1. **Download** this folder to your Desktop
2. **Open Figma** Desktop app
3. Go to **Menu → Plugins → Development → Import plugin from manifest**
4. Select the `manifest.json` file from this folder
5. Done! Access via **Menu → Plugins → Development → JSON Design Generator**

## Usage

1. Open the plugin in Figma
2. Paste your JSON data (or click an example)
3. Select a template (or use Auto Detect)
4. Click **Generate Design**

## Templates

| Template | Best For | Example |
|----------|----------|---------|
| **Auto Detect** | Let the plugin decide | Any JSON |
| **Cards Grid** | Products, profiles, features | `[{title, price, description}]` |
| **List** | Tasks, items, simple data | `[{name, value}]` |
| **Table** | Structured data, comparisons | `[{col1, col2, col3}]` |

## JSON Format

The plugin accepts:
- **Arrays**: `[{...}, {...}]`
- **Objects with items**: `{ "items": [...] }` or `{ "data": [...] }`
- **Single objects**: `{...}` (creates one item)

### Example JSONs

**Products:**
```json
[
  { "title": "Headphones", "price": "$149", "description": "Premium audio" },
  { "title": "Keyboard", "price": "$89", "description": "Mechanical switches" }
]
```

**Users:**
```json
[
  { "name": "Alice", "role": "Designer", "status": "Active" },
  { "name": "Bob", "role": "Developer", "status": "Away" }
]
```

**Pricing Table:**
```json
[
  { "plan": "Free", "price": "$0", "features": "Basic" },
  { "plan": "Pro", "price": "$19", "features": "Advanced" }
]
```

## File Structure

```
figma-json-generator/
├── manifest.json    # Plugin config (Figma reads this)
├── code.js          # Plugin logic (runs in Figma)
├── ui.html          # User interface
└── README.md        # This file
```

## Customization

### Change Default Styles

Edit `code.js` and look for these values:

```javascript
// Card styling
card.cornerRadius = 12;        // Border radius
card.paddingLeft = 20;         // Padding

// Colors (RGB 0-1 scale)
{ r: 0.18, g: 0.63, b: 0.98 }  // Blue
{ r: 0.2, g: 0.6, b: 0.4 }     // Green (prices)
```

### Add New Templates

1. Create a new async function like `generateCards()`
2. Add a case in the switch statement in `figma.ui.onmessage`
3. Add a button in `ui.html`

## Troubleshooting

**"Cannot read property 'x' of undefined"**
- Your JSON might have nested objects. Flatten them first.

**Nothing appears**
- Check if Figma canvas is zoomed out. The design appears at viewport center.

**Font error**
- The plugin uses Inter font. If not available, install it or change font family in code.js

## Next Steps (V2 Ideas)

- [ ] Connect to external APIs
- [ ] Save custom templates
- [ ] Support nested JSON
- [ ] Image URL support
- [ ] Component variants
