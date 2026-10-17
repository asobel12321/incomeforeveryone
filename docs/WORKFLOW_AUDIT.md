# Workflow audit — October 17, 2026

Scope: current `origin/main`, GitHub logs, generation, Hugo output, Netlify dispatch, public interfaces, X handling, newsletter feed, labor-data refresh, and x402 boundary checks. No parked prototypes, external sends, credential changes, or payments.

## Confirmed failures and repairs

| Layer | Evidence | Repair |
| --- | --- | --- |
| Research | October 15/16 primary runs found 1–2 eligible sources per attempt but discarded accepted candidates. October 13 both early runs failed. | Accumulate candidates, request additional unused sources, skip individual malformed dates, retain the three-source minimum. |
| Draft validation | Three URLs anywhere satisfied the old check, even without three sourced stories. | Require exactly three story blocks, each with one distinct source link. |
| Headlines | Generation allows escaped quotes; X/video readers rejected them. | Decode titles consistently in comparison, video, and X. |
| X coordination | October 13 primary timed out awaiting an article; delayed backup recovered. No deployed-page check existed. | Preserve schedule redundancy; require deployed HTML, validate dates through environment variables, restrict posting to main, fail explicitly on missing articles. |
| Receipts | Failed marker pushes had no independent receipt artifact. | Attempt marker persistence after failures and upload receipts. Recover a failed push's receipt before rerunning; artifacts alone do not prevent duplicates. |
| Newsletter | Live feed returned 200 but XML parsing failed on October 8 summary HTML entities. | Decode HTML entities and escape XML text; split CDATA terminators. Parse feeds before committing and in evening health. |
| Regression checks | No PR validation workflow; syntax check covered only paid function. | Add Python, all functions, offline payment checks, Hugo, and XML/JSON parsing. Bound scheduler dispatch fetches. |
| Handoff | Still described unmerged PR #23 and October 4 markers. | Replace with current branch, observations, and remaining work. |

## Verified baseline

- PR #23 is merged. Production latest article/committed X marker were October 16; its evening health passed. October 17 inspection occurred before the scheduled edition.
- Homepage, latest/articles APIs, JSON Feed, OpenAPI, and newsletter responded 200. Newsletter XML was malformed; successful transport was insufficient.
- Labor refresh and `--check` passed using ignored temporary outputs without changing production data.
- Premium history returned 402 with a payment challenge; malformed date returned 400 without a challenge. Offline checks passed. These checks do not prove paid fulfillment.
- Brevo records, inbox delivery, actual X playback, independent editorial verification, and ordinary-client paid settlement remain verification gaps. Missing evidence is not proof of failure.

Release validation and preview results are recorded in `SESSION_STATE.md` and the repair PR.
