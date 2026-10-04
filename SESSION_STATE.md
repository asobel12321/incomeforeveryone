# Current handoff

## Objective
Fine-tune formatting after the deployed visual-rhythm update (PR #21).

## Branch
`codex/formatting-polish`, based on current main. Parked work remains opt-in via `docs/PARKED_WORK.md`.

## Current status
Formatting fixes implemented and locally reviewed. Deployment authorized; release tracked in PR #22. Netlify preview, header and redirect checks passed; PR and Netlify metadata track publication.

## Files changed
Publication CSS, article and newsletter templates, and this handoff.

## Accomplishments
Added newsletter paragraph/button spacing and removed its nested main element. Mobile navigation wraps without hiding links. Reduced mobile headline size. Standard lists and inline links remain native; only dated daily briefs use story dividers/headings. Added source-paragraph spacing and aligned dashboard values at tablet widths. Special issues have the correct label; About no longer says Daily brief. Removed theme clipping from the homepage heading and increased its line height.

## Things tried
Reviewed local layouts at 320px, 390px, 768px and desktop widths. Checked seven page types for overflow and main landmark count.

## Things learned
Global list-item styles were affecting ordinary article lists; dated briefs need a scoped class.

## Known issues
Production rendering verification remains unresolved from earlier work. Other product tasks are in `docs/BACKLOG.md`.

## Verification run
Hugo passed (136 pages) and whitespace checks passed. At 320px, all seven reviewed pages had no horizontal overflow, visible navigation, and one main landmark. Labor values align across paired cards at 768px. Heading fix passed Hugo (136 pages) and desktop/320px visual checks.

## Next steps
After PR #22 is published, work from current main. Remaining product tasks are in docs/BACKLOG.md. Keep this handoff short.
