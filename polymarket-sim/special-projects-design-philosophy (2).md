# SPECIAL PROJECTS DESIGN PHILOSOPHY

Version 1.0 | Special Projects Studio

---

## DOCTRINE

This philosophy governs the design of technology that does not exist yet — spacecraft, autonomous systems, robotics, defense platforms, and human-machine interfaces operating at the frontier.

### First Principles Mandate

Challenge every element's existence, not its optimization. The question is never "how do we improve this?" but "should this exist at all?"

### Deletion as Design

Power comes from removing, not adding. Every element must justify its presence. The goal is maximum functionality through minimum construction.

### 1000X Over 1000x

Combine 5-10 high-leverage moves that each deliver 1000X ROI. Reject 1000 incremental optimizations that compound into nothing. One correct deletion outweighs fifty refinements.

### The Raptor Standard

Simpler construction. Lower cost. Less weight. More power. This is the measure of true design — not aesthetic novelty, but functional supremacy achieved through reduction.

### AI-Forward Architecture

All design and code must be legible to LLMs. Efficient indexing. Predictable patterns. AI will automate what humans discover. Humans will operate what AI introduces. The interface must serve both equally.

---

## CORE PRINCIPLES

**UTILITY OVER AESTHETICS**: Prioritize working functionality above all visual considerations. Cosmetic decoration is forbidden.

**GENERALIZED COMPONENTS**: Build components that support many utility types. Recycle decisions to keep the experience concise.

**MAXIMUM DENSITY**: Show as much status and functionality as possible on primary views. Operators monitor autonomous systems — they need comprehensive visibility at a glance.

**INSTANT ACCESS**: Everything must feel one click away. Solutions arrive immediately.

**EARNED PIXELS**: Every pixel must justify its presence on screen. If it cannot, delete it.

---

## LAYOUT

**MOBILE FIRST**: All layouts begin at mobile scale and expand. Never desktop-down.

**EDGE TO EDGE**: Content extends to screen edges. Avoid arbitrary inset containers.

**INLINE GROUPING**: Related functionality sits inline, never stacked vertically without purpose. Group actions that work together on the same row.

**MOBILE COLLAPSE**: When inline space is insufficient, grouped functionality collapses into a single trigger that reveals the group. Never sloppy stacking.

**DENSITY ON MONITORING**: When humans are monitoring autonomous state, maximize information density. When humans must act, dramatically reduce cognitive load to the essential interaction.

**SINGLE FOCUS**: During active interaction, focus on one task. Remove competing elements.

**NOT**: Stacking functionality vertically when it should be grouped inline. Arbitrary containers with decorative padding. Desktop-first layouts that break on mobile.

---

## SPACING

**UNITS**: 0, 8, 16, 40px only. No exceptions.

**FIELD MODE UNITS**: 0, 12, 24, 56px for hostile environments (sunlight, vibration, gloves).

**HIERARCHY THROUGH SPACE**: Use spacing to create visual grouping. Cluster related information tightly. Separate unrelated groups with larger gaps.

**ONE MOVE RULE**: If using spacing for hierarchy, do not add background color. Choose one mechanism per level of distinction.

**NOT**: 4px, 12px, 24px, 32px, or arbitrary values. Combining spacing + color + borders for the same hierarchical move.

---

## COLOR

**SYSTEM**: Three tiers of visibility only — high, medium, low.

**PALETTE (DARK MODE)**:
```
Background:   #09090B
High:         #E4E4E7  — importance, primary content
Medium:       #71717A  — state, secondary content
Low:          #3F3F46  — interactivity cues, tertiary content
Accent (AI):  #3B82F6  — automation indicators only
```

**PALETTE (LIGHT MODE)**:
```
Background:   #F4F4F5
High:         #18181B  — importance, primary content
Medium:       #52525B  — state, secondary content
Low:          #A1A1AA  — interactivity cues, tertiary content
Accent (AI):  #2563EB  — automation indicators only
```

**CONTRAST RANGE**: Content sits between 40-80% perceived contrast. Never 100% white. Never 100% black. The experience must feel muted, comfortable, and relaxed on the eyes.

**DAY/DARK MODE**: Always support both. No exceptions.

**ONE MOVE RULE**: Use only one color distinction per hierarchy level. If background color distinguishes a section, do not also add borders or extra padding.

**AUTOMATION ACCENT**: Blue (#3B82F6 dark / #2563EB light) indicates AI or automated actions. A button clicked by automation gets a blue outline. Automated content or indicators use blue. This is the only accent color in the system.

**NOT**: Gradients. Multiple accent colors. Decorative color usage. Pure black (#000000) or pure white (#FFFFFF) in standard mode.

---

## COLOR (FIELD MODE)

For hostile environments — direct sunlight, vibrating surfaces, gloved operation:

**PALETTE (DARK MODE)**:
```
Background:   #000000
High:         #FFFFFF
Medium:       #A0A0A0
Low:          #606060
Accent (AI):  #60A5FA
```

**PALETTE (LIGHT MODE)**:
```
Background:   #FFFFFF
High:         #000000
Medium:       #505050
Low:          #909090
Accent (AI):  #2563EB
```

Field mode breaks the 40-80% contrast rule intentionally for maximum legibility under duress.

---

## TYPOGRAPHY

**TYPEFACE STACK (SANS — HUMAN VOICE)**:
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

**TYPEFACE STACK (MONO — MACHINE VOICE)**:
```css
font-family: "SF Mono", "Consolas", "Liberation Mono", monospace;
```

**VOICE SYSTEM**:
- **Sans (Human)**: Labels, instructions, navigation, UI chrome, prompts, explanations, buttons, form inputs
- **Mono (Machine)**: Data, tables, comparisons, values, timestamps, system status, errors, automation indicators, metadata

If content is generated by or represents machine state, use mono. If content addresses the human or is human-authored, use sans. For mixed content (e.g., "AI completed 3 tasks in 240ms"), default to mono — it is machine voice.

**SCALE (STANDARD)**:
```
12px — metadata, tags, tertiary information
18px — body text, UI labels, primary content
20px — headings, emphasis
```

**SCALE (FIELD MODE)**:
```
16px — metadata, tags, tertiary information  
24px — body text, UI labels, primary content
28px — headings, emphasis
```

**WEIGHT**: Regular and Bold only. Use bold for hierarchy within a text block.

**METADATA BREVITY**: Keep machine voice content short. Truncate verbose state. Avoid text wrapping on status tags.

**FORM INPUTS**: Size inputs so mobile browsers do not auto-zoom on focus. Minimum 16px font size in inputs.

**NOT**: Light, medium, semibold weights. Type sizes outside the scale. Decorative typefaces. Long-form metadata that wraps.

---

## DATA FORMATTING

**NUMBERS**: Truncate to K/M/B (1,000 → 1K, 1,500,000 → 1.5M).

**TIMESTAMPS**: Local time, concise format. Prefer relative when recent ("2m ago"), absolute when historical ("Jan 5, 14:32").

**UNITS**: Always abbreviated (kg, ms, km, %). Always shown.

**EMPTY STATE**: Display "–" (en dash). Element remains visible with dash.

**ZERO STATE**: Display "0". Zero is data. Empty is absence.

**NOT**: Unformatted large numbers (1000000). Verbose timestamps (January 5th, 2026 at 2:32:45 PM UTC). Hidden elements when data is zero.

---

## INTERACTION

**TAP TARGETS (STANDARD)**: Minimum 44×44px.

**TAP TARGETS (FIELD MODE)**: Minimum 56×56px.

**HOVER STATE**: Brightness increases on hover in both light and dark mode. The element appears to come forward toward the cursor. Shift: approximately 1% brightness increase.

**CLICK STATE**: Brightness shifts 1% beyond hover. Confirms activation.

**TOUCH BEHAVIOR**: Tap skips hover state entirely. Tap toggles any hover-revealed content.

**DISABLED STATE**: Reduced opacity (40-50%). Faded appearance reserved exclusively for unavailable elements.

**CURSOR**: Never changes. Brightness shift indicates interactivity.

**ONE STATE PER ELEMENT**: Every interactive element must have hover and click states. No exceptions.

**NOT**: Scale transforms on hover. Opacity fades for active elements. Custom cursors. Hover-only functionality with no touch equivalent.

---

## HAPTICS

**PLATFORM**: Mobile touch interactions only.

**FEEL**: Mechanical and tactile. The interface should feel like operating physical controls.

**GRADUATION**:
- **Light tap**: Standard interactions (button press, toggle, select)
- **Medium tap**: Confirmations, successful completions
- **Heavy tap**: Destructive actions, errors, critical warnings

**NOT**: Haptics on scroll. Haptics on desktop. Single undifferentiated haptic for all actions.

---

## MOTION

**DURATION (LARGE)**: Maximum 200ms for page transitions, overlays, sheets, modal takeovers.

**DURATION (SMALL)**: Maximum 100ms for hovers, reveals, micro-interactions.

**EASING**: ease-out only. Elements decelerate into place.

**GOAL**: Movement should feel instant but not jarring. Fast enough to never wait, smooth enough to never startle.

**NOT**: ease-in. Linear easing. Durations over 200ms. Bounces, springs, or playful motion.

---

## STATE

**INSTANT FEEDBACK**: All state changes happen at the point of interaction. Loading indicators appear on the button pressed, not elsewhere.

**PROGRESS LANGUAGE**: For simple waits, a loading spinner on the trigger. For verbose processes, rolling text ("Loading... Caching... Collecting..."). For complex multi-step flows, a progress bar.

**SUBTLETY**: State communication must be extremely subtle. Progress indicators keep the experience feeling alive without demanding attention.

**ALIVE WHEN ACTIVE**: Show state only when processes are running. If a system is stale or idle, reduce visible information.

**TIMING VISIBILITY**: Display milliseconds for operations where performance matters. Operators must catch timing errors and bugs.

**NOT**: Global loading screens. State indicators far from the trigger. Aggressive spinners or animations. State displays that persist after completion.

---

## FAILURE

**BINARY RELIABILITY**: Systems are YES or NO. Functional or not. Confident or failed. Never "maybe." Never "80% confident." If uncertain, the answer is NO.

**FAILURE DISPLAY**: Transient notification at screen bottom. System-level feel, like a browser notification. Compact, small, unobtrusive.

**BROKEN FUNCTIONALITY**: Automatically hide broken features. Notify via subtle toast. Never show non-functional UI.

**NO REDUNDANCY**: Information appears once, in the correct location. Never displayed twice.

**NOT**: Confidence percentages. Spinning states that never resolve. Prominent error banners. Duplicate status indicators.

---

## PROGRESSIVE DISCLOSURE

**DAILY USE TEST**: If functionality is not used daily, it should be progressively disclosed.

**DISCLOSURE HIERARCHY**:
1. Visible — used constantly
2. Hover-revealed — used frequently
3. Single icon trigger — used occasionally
4. Nested menu — used rarely

**DENSITY MANAGEMENT**: When screens become too dense, shorten content and progressively disclose secondary functions. Never hide critical functionality.

**HOVER REVEALS**: Show additional status or functionality on hover. Tap toggles revealed state on touch devices.

**EMPTY CONTAINERS**: When there is nothing to show, display only the container title or "–". Do not show empty components.

**NOT**: Showing all functionality at all times. Hiding critical actions. Progressive disclosure for daily-use features.

---

## DEPTH

**GLASS**: Use glassmorphism sparingly to indicate layers. Background opacity: 80%. Content behind is visible but the glass layer remains fully legible.

**PURPOSE**: Glass indicates depth and layering without masking content abruptly. Headers, footers, and floating elements may use glass.

**SHADOWS**: 2-4% opacity shadows permitted to reduce flatness. Must be unnoticeable on conscious inspection.

**EDGE TO EDGE**: Avoid hard content cutoffs. Use transparency to maintain spatial continuity.

**RESTRAINT**: Use glass minimally to avoid compute overhead. When in doubt, use solid backgrounds.

**NOT**: Heavy drop shadows. Blur effects beyond functional glass. Multiple stacked glass layers. Decorative transparency.

---

## BORDERS

**ONE MOVE RULE**: If using borders to divide content, do not also change background color. Choose one.

**PURPOSE**: Borders help divide dense content within a shared background. They are a hierarchy tool, not decoration.

**NOT**: Borders + background color + spacing combined for the same division. Decorative borders.

---

## RADIUS

**STANDARD**: 8px only. Knocks the edge off without appearing decorative.

**FIELD MODE**: 12px for larger touch targets.

**NOT**: 4px, 16px, 24px, fully rounded, or mixed radii within the same interface.

---

## ICONS

**LIBRARY**: Phosphor Icons.

**STYLE**: Filled only. Maximum clarity and recognizability.

**COLOR**: Icons match adjacent text color. Follow the three-tier visibility system.

**NOT**: Outline icons. Mixed icon libraries. Icons in colors outside the system.

---

## HUMAN-MACHINE BOUNDARY

**SHARED INTERFACE**: Humans and AI operate in the same interface. No separate "AI view" or "human view." This enables AI to automate discovered human workflows and humans to operate AI-introduced features.

**AUTOMATION VISIBILITY**: When AI takes an action, indicate with blue accent. Blue outline on buttons clicked by automation. Blue treatment on AI-generated content or status.

**AUTHORSHIP**: Human actions have no special indicator. AI actions are always marked. Default assumption is human unless indicated otherwise.

**TRUST THROUGH CLARITY**: No confidence scores. No uncertainty indicators. Systems work or they don't. This builds trust through binary reliability, not probabilistic hedging.

**WORKFLOW EVOLUTION**: Humans discover new workflows. AI automates proven workflows. The interface must support both modes without modification.

---

## TRACEABILITY

**PRINCIPLE**: All actions are logged. All states are retrievable. Nothing is discarded.

**AUTONOMOUS AUDIT**: Every automated action must be traceable to its trigger, execution path, and outcome.

**STORAGE**: Everything created must be accessible again in the future. This supports analytics, debugging, incident review, and regulatory compliance.

**FUTURE DEVELOPMENT**: This section will expand as traceability patterns mature. The commitment is absolute — implementation details will evolve.

---

## QUICK REFERENCE

### Standard Mode
```
Spacing:     0, 8, 16, 40px
Type:        12, 18, 20px
Radius:      8px
Tap target:  44px min
Motion:      <200ms large, <100ms small
Glass:       80% opacity
```

### Field Mode
```
Spacing:     0, 12, 24, 56px
Type:        16, 24, 28px
Radius:      12px
Tap target:  56px min
Motion:      <200ms large, <100ms small
Glass:       80% opacity
```

### Color (Dark)
```
Background:  #09090B
High:        #E4E4E7
Medium:      #71717A
Low:         #3F3F46
Accent:      #3B82F6
```

### Color (Light)
```
Background:  #F4F4F5
High:        #18181B
Medium:      #52525B
Low:         #A1A1AA
Accent:      #2563EB
```

### Type Stack
```css
/* Human voice */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

/* Machine voice */
font-family: "SF Mono", "Consolas", "Liberation Mono", monospace;
```

---

## DECISION FILTER

Before adding any element, ask:

1. Can this be deleted entirely?
2. Can this be combined with an existing component?
3. Does this represent a 1000X move or a 1x optimization?
4. Does this earn its pixels?
5. Will this be used daily?
6. Can a human and AI both operate this?
7. Is this one move or multiple moves disguised as one?

If uncertain on any answer, delete the element.

---

© Special Projects Studio
