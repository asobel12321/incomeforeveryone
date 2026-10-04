# Current handoff

## Objective
Clean the active project context and correct newsletter cadence. Keep parked work recoverable without treating it as active scope.

## Branch
Release baseline: `main`. Cleanup branch: `codex/project-cleanup`; use Git status for the active branch. Old shared edits are archived, not pending release.

## Current status
Cleanup implemented and locally verified. GitHub tracks its release from `codex/project-cleanup`. Authoritative remaining work is in `docs/BACKLOG.md`.

## Files changed
Shortened AGENTS/README/project map/newsletter/x402 documentation; added backlog and parked-work index; removed completed audit/checklist, duplicate OpenAPI draft and starter files; untracked generated `public/`; fixed weekly newsletter copy and OpenAPI source pointer.

## Accomplishments
Preserved the old shared checkout in `codex/archive-shared-20261004`; committed the premium prototype locally as `codex/parked-premium-labor-data` (`2c26580`). Weekly dashboard remains preserved on `codex/layoff-hiring-signal` (`a6f7fed`). No prototype was published.

## Things tried
Reconciled from current main instead of replaying obsolete local copies. Historical material is in Git refs, not the routine agent reading path.

## Things learned
Newsletter delivery is weekly, while article publication is daily. Production x402 setup is complete; normal-client paid fulfillment is a verification gap, not an unstarted setup project.

## Known issues
Production headline verification remains blocked by the prior browser approval failure. First newsletter campaign and next generated brief still need review. See the backlog; do not reload old transcripts to reconstruct it.

## Verification run
Hugo passed (135 pages); function checks, offline x402 checks, all 35 Python tests, and Git whitespace checks passed. Built newsletter HTML contains Wednesday delivery copy. Production browser verification remains unconfirmed.

## Next steps
Work from current main after the cleanup release. Keep this file short and replace stale status rather than appending history. Choose next work from the backlog; parked code requires an explicit resume decision.
