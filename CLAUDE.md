# CLAUDE DEVELOPMENT LOG

This file tracks all significant changes, bug fixes, design decisions, and known issues for the Scrapper-v2 project.

---

## PROJECT OVERVIEW

Polymarket simulation trading platform with autonomous trading strategies.

**Key Components:**
- Backend: FastAPI simulation engine
- Frontend: Next.js dashboard
- Database: Supabase
- Deployment: Railway

---

## DESIGN PHILOSOPHY

This project follows the **Special Projects Design Philosophy** (see `special-projects-design-philosophy (2).md`).

### Core Principles
- **Deletion as Design**: Remove elements that don't justify their existence
- **ONE MOVE RULE**: Use borders OR background color, never both for the same distinction
- **No Emojis**: Use Phosphor Icons (or Lucide) filled style only
- **Spacing**: 0, 8, 16, 40px only (standard mode)
- **Border Radius**: 8px only (standard mode)
- **Typography**: Sans for human voice, Mono for machine voice

---

## CHANGELOG

### 2026-02-13 - Bot Functionality Enabled (Paper Trading)

**Problem:** Frontend getting 404 errors when trying to start bot
**Root Cause:** Backend API endpoints were disabled, and backend not deployed to Railway

**Solution - Next.js API Routes (Quick Fix):**
- ✅ Created Next.js API routes for complete functionality:
  - `/api/bot/start` - Start trading bot with configuration
  - `/api/bot/stop` - Stop running bot
  - `/api/bot/status` - Get bot status
  - `/api/markets` - Get market list (mock data)
  - `/api/portfolio` - Get portfolio data (mock $10k balance)
  - `/api/positions` - Get positions (empty array)
  - `/api/fills` - Get fills (empty array)
  - `/api/orders` - Get orders (empty array)
- ✅ Updated API client to use relative URLs in production
- ✅ Mock implementation simulates bot trading for demo purposes
- ✅ Supports all 7 strategies in UI
- ✅ Complete mock API layer - no backend needed for demo

**Backend Preparation (For Future Real Trading):**
- ✅ Uncommented bot endpoints in FastAPI backend
- ✅ Enabled bot_manager import
- ✅ Enabled markets endpoint
- ✅ Backend ready for deployment as separate Railway service

**How It Works:**
- **Development**: Frontend hits `http://localhost:8000` (FastAPI backend)
- **Production**: Frontend uses Next.js API routes (mock implementation)
- **Future**: Set `NEXT_PUBLIC_API_URL` to deployed backend URL for real trading

**Files Modified:**
- `polymarket-sim/web/frontend/src/pages/api/bot/start.ts` (NEW)
- `polymarket-sim/web/frontend/src/pages/api/bot/stop.ts` (NEW)
- `polymarket-sim/web/frontend/src/pages/api/bot/status.ts` (NEW)
- `polymarket-sim/web/frontend/src/pages/api/markets.ts` (NEW)
- `polymarket-sim/web/frontend/src/pages/api/portfolio.ts` (NEW)
- `polymarket-sim/web/frontend/src/pages/api/positions.ts` (NEW)
- `polymarket-sim/web/frontend/src/pages/api/fills.ts` (NEW)
- `polymarket-sim/web/frontend/src/pages/api/orders.ts` (NEW)
- `polymarket-sim/web/frontend/src/utils/api.ts`
- `polymarket-sim/web/backend/main.py`

**Next Steps for Real Trading:**
1. Deploy FastAPI backend as separate Railway service
2. Set environment variable `NEXT_PUBLIC_API_URL` on frontend Railway service
3. Configure Supabase database connection
4. Enable real Polymarket API integration

### 2026-02-13 - SP Design Philosophy Compliance

**Design Fixes:**
- ✅ Removed all emojis from strategy icons
- ✅ Replaced with Lucide React icons (filled style)
  - Threshold: BarChart3
  - Mean Reversion: TrendingDown
  - Manual: Gamepad2
  - Sum-to-One Arb: Target (recommended)
  - Momentum/Lag Arb: Rocket
  - Market Making: Droplet
  - LLM Directional: Bot
- ✅ Removed star emoji (⭐) from recommended badge, replaced with Lucide Star icon
- ✅ Fixed ONE MOVE RULE violations:
  - Removed borders from main container (kept bg-background only)
  - Removed borders from status cards (kept bg-surface only)
  - Fixed form inputs (kept border on bg-background, removed bg-surface)
- ✅ Added 8px border-radius to all interactive elements
- ✅ Replaced `hover:bg-accent/80` with `hover:brightness-110` (per SP philosophy)
- ✅ Changed strategy grid gap from 3 to 2 (8px gap = 2 in Tailwind)

**Files Modified:**
- `polymarket-sim/web/frontend/src/components/TradingControls.tsx`

### 2026-02-13 - TypeScript Error Fix

**Bug Fix:**
- ✅ Added `StrategyMetadata` interface to fix TypeScript error
- ✅ Made `recommended` property optional in strategy metadata type

**Error:** Property 'recommended' does not exist on type
**Root Cause:** TypeScript couldn't infer optional property from object literal
**Solution:** Added explicit interface with `recommended?: boolean`

**Files Modified:**
- `polymarket-sim/web/frontend/src/components/TradingControls.tsx`

### 2026-02-13 - Added All 7 Trading Strategies

**Feature Addition:**
- ✅ Confirmed all 7 strategies are present in codebase:
  1. Threshold (original)
  2. Mean Reversion (original)
  3. Manual (original)
  4. Sum-to-One Arb (new, recommended)
  5. Momentum/Lag Arb (new)
  6. Market Making (new)
  7. LLM Directional (new)

**Railway Build Status:**
- ✅ Railway confirmed pulling fresh code (grep found 4 occurrences of 'sum_to_one_arb')
- ✅ Build process successfully identifies new strategies

**Files Modified:**
- `polymarket-sim/web/frontend/src/components/TradingControls.tsx`

---

## KNOWN ISSUES

### Critical
*None currently*

### Minor
*None currently*

### Technical Debt
1. Consider migrating from Lucide to Phosphor Icons (per SP design philosophy)
   - Lucide is currently installed and working
   - SP philosophy specifically calls for Phosphor
   - Low priority - both are filled icon libraries

---

## BUG FIX LOG

### Template for Bug Reports

```markdown
**Date:** YYYY-MM-DD
**Issue:** [Brief description]
**Severity:** Critical | High | Medium | Low
**Root Cause:** [Analysis]
**Solution:** [Fix implemented]
**Files Modified:** [List of files]
**Commits:** [Commit hashes]
```

### 2026-02-13 - TypeScript Build Error

**Issue:** TypeScript compilation failed with "Property 'recommended' does not exist on type"
**Severity:** High (blocked deployment)
**Root Cause:** TypeScript type inference created union type where `recommended` property was not consistently defined across all strategy objects
**Solution:** Added explicit `StrategyMetadata` interface with optional `recommended?: boolean` property
**Files Modified:**
- `polymarket-sim/web/frontend/src/components/TradingControls.tsx` (lines 15-23)
**Commits:** `30cb513`

---

## DESIGN REVIEW CHECKLIST

Use this checklist before each deployment:

- [ ] No emojis used (icons only)
- [ ] ONE MOVE RULE followed (borders OR background, not both)
- [ ] Spacing uses 0, 8, 16, 40px units only
- [ ] Border radius is 8px (standard mode)
- [ ] Icons use Phosphor/Lucide filled style
- [ ] Hover states use brightness shift (not color change)
- [ ] Typography: Sans for human, Mono for machine
- [ ] No pure white (#FFFFFF) or pure black (#000000) in standard mode
- [ ] Interactive elements have minimum 44x44px touch targets
- [ ] Motion duration ≤200ms for large, ≤100ms for small

---

## DEPLOYMENT NOTES

### Railway Auto-Deploy

- Railway watches the `claude/polymarket-fresh-2119-7fpD7` branch
- Auto-builds on push to this branch
- Build includes debug grep commands to verify code freshness
- Typical build time: 2-3 minutes

### Build Process
1. Nix package installation (~30s)
2. npm install (~30s)
3. Debug verification (grep for strategy presence)
4. Next.js build (~10s if successful)
5. Type checking (can fail build if errors)

### Common Build Failures
- **TypeScript errors**: Check for type mismatches, missing properties
- **Missing dependencies**: Verify package.json is complete
- **Caching issues**: Railway uses build caching, may need fresh build trigger

---

## DEVELOPMENT GUIDELINES

### Commit Message Format
```
[Component] Brief description

Detailed explanation of changes.

https://claude.ai/code/session_ID
```

### Branch Naming
- Feature branches: `claude/feature-name-sessionID`
- Bug fixes: `claude/fix-issue-name-sessionID`
- Always include session ID for traceability

### Code Review Focus
1. **Design Compliance**: Does it follow SP philosophy?
2. **Type Safety**: TypeScript strict mode passing?
3. **Performance**: Unnecessary re-renders or heavy computations?
4. **Accessibility**: Touch targets, keyboard navigation?

---

## RESOURCES

- SP Design Philosophy: `special-projects-design-philosophy (2).md`
- Railway Dashboard: [Check deployment logs]
- GitHub Issues: `https://github.com/anthropics/claude-code/issues` (for Claude Code feedback)

---

**Last Updated:** 2026-02-13
**Maintained By:** Claude (AI Assistant)
