# Labor Stats x402 Prep

## Boundary

- Public: `/labor-stats/` and `/api/labor-stats/` keep serving the latest curated labor-market snapshot with source URLs, release URLs, period labels, and interpretation text.
- Paid candidate: `/api/labor-stats/history` should serve historical snapshots, revision notes, deltas, and agent-oriented comparison metadata.
- Rationale: the public site remains useful and citable, while paid access monetizes machine-friendly history and higher-volume analytical use.

## Runtime Architecture

The current public API is static Hugo output. A paid x402 route needs request-time behavior because the server must return `402 Payment Required`, read `PAYMENT-SIGNATURE`, verify/settle the payment, and only then return premium JSON. Use a Netlify Function for the paid route unless the site later moves to a broader server runtime.

The function at `netlify/functions/labor-stats-history.mjs` uses `@x402/core` and `@x402/evm` for request-time payment challenge, verification, settlement, and `PAYMENT-RESPONSE` headers. It is disabled by default and must not return production premium data until these are explicitly configured in Netlify:

- `X402_LABOR_STATS_ENABLED=true`
- `X402_PAY_TO`
- `X402_FACILITATOR_URL`

Optional production overrides:

- `X402_NETWORK` defaults to `eip155:8453`.
- `X402_ASSET` defaults to Base USDC, `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, when the network is Base mainnet.
- `X402_AMOUNT_ATOMIC` defaults to `10000`, equal to `$0.01` for 6-decimal USDC.
- `X402_ASSET_NAME` defaults to `USD Coin`.
- `X402_ASSET_VERSION` defaults to `2`.

Before production launch, confirm the facilitator supports the selected network and asset. Do not treat the public test facilitator as the production default.

For local payload testing only, the function returns `data/labor_stats_history.json` when `NETLIFY_DEV=true` or when `X402_LABOR_STATS_DEV_BYPASS=true` outside production. This bypass is intentionally marked in the JSON response and must not be used as production access control.

## Verification

Run the local function checks before changing paid-route behavior:

```powershell
npm.cmd run check:functions
npm.cmd run check:x402
```

`npm.cmd run check:x402` verifies the disabled production-default response, local/dev bypass response, method rejection, and premium payload shape. It does not hit the network by default.

To verify that configured x402 mode emits a real SDK challenge against the public testnet facilitator:

```powershell
$env:CHECK_X402_TESTNET_CHALLENGE='true'; npm.cmd run check:x402; Remove-Item Env:CHECK_X402_TESTNET_CHALLENGE
```

That test uses a dummy pay-to address and Base Sepolia USDC metadata. It proves challenge generation, not production settlement.

## Production Preview Runbook

Keep this route disabled until the receiving wallet and facilitator are intentionally chosen. Configure values in Netlify, not in repository files.

1. Choose the production payment values:
   - `X402_PAY_TO`: receiving wallet address.
   - `X402_FACILITATOR_URL`: production facilitator endpoint or self-facilitator endpoint.
   - Confirm whether the defaults are acceptable: `X402_NETWORK=eip155:8453`, Base USDC asset `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, and `X402_AMOUNT_ATOMIC=10000`.
2. Add Netlify environment variables scoped to a deploy-preview or branch context first:
   - `X402_LABOR_STATS_ENABLED=true`
   - `X402_PAY_TO`
   - `X402_FACILITATOR_URL`
   - Optional overrides: `X402_NETWORK`, `X402_ASSET`, `X402_AMOUNT_ATOMIC`, `X402_ASSET_NAME`, `X402_ASSET_VERSION`
3. Trigger a fresh PR #3 deploy preview after the variables are present.
4. Probe the preview route without payment credentials:

```powershell
$preview = "https://deploy-preview-3--incomeforeveryone.netlify.app"
curl.exe -i "$preview/api/labor-stats/history"
```

Expected result: status `402` and a non-empty `PAYMENT-REQUIRED` header. If the route returns `503`, configuration is still missing. If it returns `200` without payment, stop and disable the route before continuing.

5. Decode the `PAYMENT-REQUIRED` header and confirm the resource, network, asset, amount, and pay-to address match the chosen production values.
6. Only after preview behavior is correct, publish the final OpenAPI contract at `/openapi.json` and run x402scan/Merit discovery checks.

## History Payload

`scripts/refresh_labor_stats.py` writes `data/labor_stats_history.json` alongside the public snapshot. The history payload currently includes:

- 13 recent monthly observations per indicator.
- Display and raw values for each observation.
- Month-over-month changes where a prior observation exists.
- Latest deltas per indicator.
- Source metadata copied from the public snapshot.
- An empty `revisions` array reserved for later revision tracking.

## Candidate Pricing

- Mode: fixed
- Price: `$0.01` per successful premium request
- Currency: USD, settled via x402-compatible stablecoin rails
- Initial network target: Base USDC, represented as `eip155:8453`

This price is intentionally low enough for agentic discovery and repeated calls, while preserving a clear difference from the free snapshot endpoint.

## Listing Prep

x402scan/Merit discovery guidance currently expects OpenAPI as the canonical contract, with `x-payment-info` on payable operations and runtime 402 behavior matching the metadata. Keep the draft OpenAPI in `docs/labor-stats-x402-openapi-draft.json` until the runtime route is fully enforcing payments.

Registration readiness checklist:

- Publish the final OpenAPI contract at `/openapi.json`.
- Include `info.x-guidance` and a real contact email if listing ownership should be verified.
- Ensure the paid operation declares `x-payment-info`, `responses.402`, and a JSON response schema.
- Ensure probing `/api/labor-stats/history` reaches a real x402 `402` challenge before any body/query validation failure.
- Run discovery checks before registration:
  - `npx -y @agentcash/discovery@latest discover "https://incomeforeveryone.org"`
  - `npx -y @agentcash/discovery@latest check "https://incomeforeveryone.org/api/labor-stats/history"`

## Sources Checked

- x402 docs: server responds with `402 Payment Required`, clients retry with `PAYMENT-SIGNATURE`, and servers verify/settle before returning the resource.
- x402 docs: facilitators reduce server-side blockchain complexity, but production routes need an explicit mainnet facilitator/self-facilitation choice.
- x402scan discovery docs: OpenAPI is the canonical discovery contract, paid operations need `x-payment-info`, and runtime 402 behavior is authoritative.
