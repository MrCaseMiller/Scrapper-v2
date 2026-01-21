# JSON Guide for Dynamic Table Generator

Create JSON files that render perfectly in the Figma table plugin.

---

## Golden Rule

**Keep it flat.** One level of key-value pairs per item. No nested objects.

```json
[
  { "name": "Alpha", "status": "Active", "value": "$100" },
  { "name": "Beta", "status": "Pending", "value": "$200" }
]
```

---

## Quick Templates

### Simple List
```json
[
  { "name": "", "status": "", "value": "" },
  { "name": "", "status": "", "value": "" }
]
```

### Product/Service Comparison
```json
[
  {
    "product": "",
    "category": "",
    "price": "",
    "features": "",
    "rating": ""
  }
]
```

### Company/Competitor Analysis
```json
[
  {
    "company": "",
    "type": "",
    "headquarters": "",
    "founded": "",
    "funding": "",
    "revenue": "",
    "employees": "",
    "key_product": "",
    "target_market": ""
  }
]
```

### Feature Matrix
```json
[
  {
    "feature": "",
    "product_a": "Yes/No",
    "product_b": "Yes/No",
    "product_c": "Yes/No",
    "notes": ""
  }
]
```

### Pricing Table
```json
[
  {
    "plan": "",
    "price": "",
    "users": "",
    "storage": "",
    "support": "",
    "features": ""
  }
]
```

### Task/Project Tracker
```json
[
  {
    "task": "",
    "owner": "",
    "status": "",
    "priority": "",
    "due_date": "",
    "notes": ""
  }
]
```

---

## Structure Rules

### DO ✓

```json
[
  {
    "company": "Acme Inc",
    "revenue": "$50M",
    "employees": "500",
    "status": "Active"
  }
]
```

- Use an array `[]` at the root (or wrap in `{"items": [...]}`)
- Keep all values as strings or numbers
- Use consistent keys across all items
- Use short, descriptive key names (snake_case preferred)

### DON'T ✗

```json
[
  {
    "company": "Acme Inc",
    "financials": {
      "revenue": "$50M",
      "profit": "$5M"
    },
    "locations": ["NYC", "LA", "London"]
  }
]
```

- Avoid nested objects (flatten them instead)
- Avoid arrays as values (join them: `"NYC, LA, London"`)
- Avoid inconsistent keys between items

---

## Flattening Nested Data

### Before (Nested - Bad)
```json
{
  "company": "Acme",
  "financials": {
    "revenue": "$50M",
    "funding": "$100M"
  },
  "facilities": {
    "hq": "New York",
    "size": "50,000 sq ft"
  }
}
```

### After (Flat - Good)
```json
{
  "company": "Acme",
  "revenue": "$50M",
  "funding": "$100M",
  "headquarters": "New York",
  "facility_size": "50,000 sq ft"
}
```

---

## Handling Arrays

### Before (Array - Bad)
```json
{
  "company": "Acme",
  "partners": ["Google", "Microsoft", "Apple"]
}
```

### After (String - Good)
```json
{
  "company": "Acme",
  "partners": "Google, Microsoft, Apple"
}
```

---

## Column Naming Tips

| Instead of | Use |
|------------|-----|
| `val` | `value` |
| `desc` | `description` |
| `qty` | `quantity` |
| `amt` | `amount` |
| `loc` | `location` |
| `hq` | `headquarters` |
| `yoy_growth` | `growth_yoy` |

The plugin converts `snake_case` to `Title Case` automatically:
- `total_funding` → "Total Funding"
- `key_partners` → "Key Partners"

---

## Wrapper Formats

The plugin auto-detects arrays in these wrapper formats:

```json
{ "items": [...] }
{ "data": [...] }
{ "results": [...] }
{ "products": [...] }
{ "competitors": [...] }
{ "users": [...] }
{ "rows": [...] }
{ "list": [...] }
{ "records": [...] }
{ "entries": [...] }
```

---

## Recommended Column Count

| Use Case | Columns | Notes |
|----------|---------|-------|
| Quick list | 3-4 | Name, status, value |
| Comparison | 5-8 | Key differentiators |
| Full analysis | 10-14 | Comprehensive view |
| Max readable | 14-16 | Beyond this, select columns |

---

## Empty Values

Use `-` or leave empty for missing data:

```json
{
  "company": "Startup Inc",
  "revenue": "-",
  "funding": "$5M",
  "valuation": ""
}
```

Both `-` and `""` render as `-` in the table.

---

## Full Example: Competitor Analysis

```json
[
  {
    "company": "Company A",
    "type": "Enterprise",
    "headquarters": "San Francisco, CA",
    "founded": "2015",
    "total_funding": "$150M",
    "latest_round": "Series C - $80M",
    "revenue": "$45M ARR",
    "employees": "350",
    "primary_product": "Analytics Platform",
    "target_market": "Fortune 500",
    "key_differentiator": "AI-powered insights",
    "notable_customers": "Nike, Uber, Spotify"
  },
  {
    "company": "Company B",
    "type": "Startup",
    "headquarters": "New York, NY",
    "founded": "2020",
    "total_funding": "$25M",
    "latest_round": "Series A - $18M",
    "revenue": "$5M ARR",
    "employees": "45",
    "primary_product": "Data Pipeline",
    "target_market": "Mid-market",
    "key_differentiator": "No-code interface",
    "notable_customers": "Warby Parker, Glossier"
  }
]
```

---

## Quick Checklist

Before pasting JSON into the plugin:

- [ ] Root is an array `[...]` or wrapped object
- [ ] All items have the same keys
- [ ] No nested objects (flattened)
- [ ] No array values (joined as strings)
- [ ] Keys use `snake_case`
- [ ] Values are strings or numbers
- [ ] Empty values use `-` or `""`

---

## ChatGPT/Claude Prompt

Use this prompt to generate table-ready JSON:

```
Create a JSON array for a comparison table with these requirements:
- Flat structure (no nested objects)
- Consistent keys across all items
- Use snake_case for key names
- Join any lists as comma-separated strings
- Use "-" for missing values

Topic: [YOUR TOPIC]
Items to compare: [LIST ITEMS]
Data points needed: [LIST COLUMNS]
```
