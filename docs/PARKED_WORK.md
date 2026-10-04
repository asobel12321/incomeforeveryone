# Parked work and recovery

Do not load these branches/worktrees in routine tasks. Neither prototype is approved for release. Preserve the refs; resume only at the user's request.

| Item | Recoverable local ref | State |
| --- | --- | --- |
| Weekly Layoff + Hiring Signal | `codex/layoff-hiring-signal` at `a6f7fed` | Curated data, generator, proposed article, source assessment. Needs fresh inputs, editorial decision, and integration with current main. No complete official weekly national completed-layoff count was identified; WARN would be a separate planned-announcement signal. |
| Expanded premium labor data | `codex/parked-premium-labor-data` at `2c26580` | History from 2019, derived metrics, freshness metadata, three composite indexes. Preserved from uncommitted July work; needs methodology review and integration with newer payment/filter protections. |
| Pre-cleanup shared checkout | `codex/archive-shared-20261004` at `d1b7fbafc7d61f076aa1ffdf2ca82594f4a396f6` | Local stash-shaped snapshot of tracked and untracked work, including full historical handoff and October 4 audit. Not a release branch. |

Recovery is selective: inspect a ref with `git show REF:path`; the shared snapshot's untracked files are in `REF^3:path`. For example, the old audit is `codex/archive-shared-20261004^3:docs/PROJECT_STATUS_2026-10-04.md`. Do not apply the full snapshot onto main: it would restore obsolete code and generated output. These refs are local, not off-device backups.

Completed release branches and historical documentation remain in Git history. Earlier daily-newsletter/manual-draft plans, Zira/OpenAI production-voice experiments, and the generic article deck have been superseded. Current operation is weekly Brevo delivery and Kokoro Michael X narration. They are not unfinished integrations.
