# Ranking Reference Trust Copy Design

## Summary

Refine the ranking-reference presentation so the module feels more trustworthy and easier to interpret without changing the API or data model.

The current `参考榜单` section already shows source-backed ranking entries, but the copy is still fairly bare. We should tighten the display language so users can more easily tell what they are looking at, where it came from, and how much weight to place on it.

## Goals

- Add a light trust-oriented hint to the ranking-reference section.
- Make the source link language more explicit.
- Keep ranking cards visually and semantically consistent.
- Avoid expanding this into a scoring or source-classification system.

## Non-Goals

- Changing the `ranking_references` API shape
- Adding source credibility scoring
- Adding ranking filtering, sorting, or comparison
- Building a dedicated ranking source registry

## Recommended Approach

Keep the current ranking-reference data shape and improve only the presentation layer:

- add a short section-level hint: `不同榜单口径不同，结果仅供参考。`
- keep the first line as `来源 + 年份`
- keep the main result label prominent
- change the link copy from `查看来源` to `查看来源原文`

This is the best fit for the current stage because it meaningfully improves interpretability without adding new data requirements or backend complexity.

## Alternatives Considered

### Add only a disclaimer

This is the smallest change, but it leaves the rest of the module language under-specified and does not improve the source-action wording.

### Add credibility scores or badges

This sounds useful, but we do not have the data model or editorial standards to support it honestly yet. It would create more implied authority than we can defend.

## Current State

The ranking-reference module currently supports:

- source and year
- result label
- optional scope
- optional note
- optional source link

But it does not yet communicate:

- that different ranking methodologies vary
- that the result should be treated as one reference signal
- that the link leads to the original source material

## Presentation Changes

### Section-level hint

When ranking references exist, show this hint beneath the `参考榜单` title:

- `不同榜单口径不同，结果仅供参考。`

This hint should not appear when the section itself is absent.

### Link wording

When a ranking reference has a `url`, the link label should be:

- `查看来源原文`

This is clearer than `查看来源` because it describes the destination more precisely.

### Card order

Each ranking-reference card should continue to render in this order:

1. `source + year`
2. `label`
3. optional `scope`
4. optional `note`
5. optional `查看来源原文` link

## Architecture

### `apps/web/components/public/ranking-reference-list.tsx`

This component should remain the single place where ranking-reference display copy is defined.

Changes should stay presentation-only:

- add the section hint
- update the link copy
- preserve current card structure

### Detail pages

School and major detail pages should remain unchanged except for consuming the updated shared component.

## Testing Strategy

### Web tests

Update `apps/web/tests/public-pages.test.tsx` so it verifies:

- `参考榜单` appears when ranking references exist
- the section hint text appears when references exist
- the source link label is `查看来源原文`
- the section and hint are absent when ranking references are empty

### Verification

- targeted Vitest run for `tests/public-pages.test.tsx`
- full `apps/web` Vitest run
- `next build` in `apps/web`

## Risks And Mitigations

### Risk: the trust hint feels too strong or too repetitive

Mitigation:
- keep it short and neutral
- render it once at the section level, not on every card

### Risk: users may still over-read one ranking source

Mitigation:
- explicitly frame the section as `参考榜单`
- explicitly say `结果仅供参考`

## Completion Criteria

- The ranking-reference section includes a short trust hint when rendered.
- Source links use `查看来源原文`.
- The section stays hidden when no ranking references exist.
- Web tests and build pass.
