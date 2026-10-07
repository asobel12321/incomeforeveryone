# Session State

## Objective
Repair daily publication failures observed October 5-6.

## Branch
`codex/publishing-reliability`, based on `origin/main`; release PR #23.

## Current Status
Repair tested locally and in an artifact-only GitHub run; release verification in progress.

## Files Changed
Daily generation script/tests, article and health workflows, README, and this handoff.

## Accomplishments
Separate research from drafting; exclude prior URLs before selection, require completed search and recent source dates, constrain draft links, and retain blocking validation. Add bounded retries and safe branch previews. Resolve edition date once. Evening health flags the first missed edition and reads current main markers.

## Things Tried
Live preview 37627916148 passed article generation, video-script generation, and Hugo. Preview artifact source links were reviewed. Netlify PR preview, headers, and redirects passed.

## Things Learned
October 5-6 article runs rejected reused sources; X timed out waiting for missing articles. Prompt-only exclusions still failed live, so research selection now precedes drafting. Labor refresh remained healthy.

## Known Issues
Production latest article and X marker were October 4 at initial inspection. Newsletter feed works; first scheduled Brevo delivery October 7 remains unverified. Automated research checks do not independently verify claims or dates.

## Verification Run
Python compilation passed; 39 Python tests passed; Hugo passed (136 pages); whitespace checks passed. Live preview passed. Production labor-data freshness and full-content newsletter feed passed read-only checks.

## Next Steps
Release PR #23, verify current article deployment and normal X run. Do not backdate invented editions. Verify first Brevo campaign separately without sending tests or changing recipients.
