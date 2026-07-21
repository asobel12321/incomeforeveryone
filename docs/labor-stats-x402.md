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
- `X402_FACILITATOR_AUTH_HEADER_NAME` and `X402_FACILITATOR_AUTH_HEADER_VALUE` add one optional auth header to facilitator `supported`, `verify`, `settle`, and Bazaar requests. Use these only in Netlify environment settings if the chosen production facilitator requires API-key or bearer-token auth.

Before production launch, confirm the facilitator supports the selected network and asset. Do not treat the public test facilitator as the production default.

Candidate production facilitator values to evaluate:

- Coinbase CDP x402: `https://api.cdp.coinbase.com/platform/v2/x402`
- PayAI: `https://facilitator.payai.network`

The official x402 docs list the default `https://x402.org/facilitator` as a testing/development facilitator for Base Sepolia and other testnets, not the production Base mainnet default.

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
   - `X402_FACILITATOR_URL`: production facilitator endpoint or self-facilitator endpoint. Current candidates to evaluate are Coinbase CDP x402 and PayAI.
   - Confirm whether the defaults are acceptable: `X402_NETWORK=eip155:8453`, Base USDC asset `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, and `X402_AMOUNT_ATOMIC=10000`.
2. Add Netlify environment variables scoped to a deploy-preview or branch context first:
   - `X402_LABOR_STATS_ENABLED=true`
   - `X402_PAY_TO`
   - `X402_FACILITATOR_URL`
   - Optional overrides: `X402_NETWORK`, `X402_ASSET`, `X402_AMOUNT_ATOMIC`, `X402_ASSET_NAME`, `X402_ASSET_VERSION`
   - Optional facilitator auth: `X402_FACILITATOR_AUTH_HEADER_NAME`, `X402_FACILITATOR_AUTH_HEADER_VALUE`
3. Trigger a fresh PR #3 deploy preview after the variables are present.
4. Probe the preview route without payment credentials:

```powershell
$preview = "https://deploy-preview-3--incomeforeveryone.netlify.app"
curl.exe -i "$preview/api/labor-stats/history"
```

Expected result: status `402` and a non-empty `PAYMENT-REQUIRED` header. If the route returns `503`, configuration is still missing. If it returns `200` without payment, stop and disable the route before continuing.

5. Decode the `PAYMENT-REQUIRED` header and confirm the resource, network, asset, amount, and pay-to address match the chosen production values.
6. After preview behavior is correct, publish the final OpenAPI contract at `/openapi.json` and run x402scan/Merit discovery checks.

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

x402scan/Merit discovery guidance currently expects OpenAPI as the canonical contract, with `x-payment-info` on payable operations and runtime 402 behavior matching the metadata. The reviewed contract source lives in `docs/labor-stats-x402-openapi-draft.json` and is published to `static/openapi.json` for preview discovery after runtime x402 challenge behavior was confirmed.

Registration readiness checklist:

- Publish the final OpenAPI contract at `/openapi.json`.
- Include `info.x-guidance` and a real contact email if listing ownership should be verified.
- Tighten request/response schemas enough for agent invocation. Merit's current discovery tooling warns that endpoints without useful input/output schemas may be skipped or treated as non-invocable.
- Ensure the paid operation declares `x-payment-info`, `responses.402`, and a JSON response schema.
- Ensure probing `/api/labor-stats/history` reaches a real x402 `402` challenge before any body/query validation failure.
- Runtime challenge compatibility: unpaid x402 challenges keep the SDK-standard `PAYMENT-REQUIRED` header and also send `WWW-Authenticate: x402` for Merit/x402scan discovery compatibility.
- Run discovery checks before registration:
  - `npx -y @agentcash/discovery@latest discover "https://incomeforeveryone.org"`
  - `npx -y @agentcash/discovery@latest check "https://incomeforeveryone.org/api/labor-stats/history"`

Discovery-tool baseline against PR #3 deploy preview before publishing `/openapi.json` and before setting deploy-preview x402 env vars:

- `npx.cmd -y @agentcash/discovery@latest discover "https://deploy-preview-3--incomeforeveryone.netlify.app"` returned `OPENAPI_NOT_FOUND`, as expected.
- `npx.cmd -y @agentcash/discovery@latest check "https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history"` returned `L3_NOT_FOUND`, as expected while the paid route is disabled instead of emitting a production `402`.

Current preview state after setting deploy-preview x402 env vars:

- `/api/labor-stats/history` returns a real `402 Payment Required` challenge with `PAYMENT-REQUIRED` and `WWW-Authenticate: x402`.
- `/openapi.json` is now published for discovery checks on deploy previews.
- The live x402 challenge includes Bazaar input/output schema metadata at `extensions.bazaar.schema.properties.input.properties.queryParams` and `extensions.bazaar.schema.properties.output.properties.example`.
- `npx.cmd -y @agentcash/discovery@latest discover "https://deploy-preview-3--incomeforeveryone.netlify.app"` passes with no warnings, finds `/api/labor-stats` as `unprotected`, and marks `/api/labor-stats/history` as `paid 0.010000 USD [x402]`.
- `npx.cmd -y @agentcash/discovery@latest check "https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history"` passes cleanly for the paid route.

## Sources Checked

- x402 docs: server responds with `402 Payment Required`, clients retry with `PAYMENT-SIGNATURE`, and servers verify/settle before returning the resource.
- x402 docs: facilitators reduce server-side blockchain complexity, but production routes need an explicit mainnet facilitator/self-facilitation choice.
- x402 docs: the default x402.org facilitator is recommended for testing/development and supports Base Sepolia; production Base mainnet needs a production facilitator such as Coinbase CDP x402 or PayAI.
- x402scan discovery docs: OpenAPI is the canonical discovery contract, paid operations need `x-payment-info`, and runtime 402 behavior is authoritative.
- x402scan discovery docs: current tooling checks `/openapi.json`, requires `info.x-guidance`, recommends `info.contact.email`, expects paid operations to declare `x-payment-info` and `402`, and can skip endpoints without useful schemas.
- x402scan quickstart: current guidance says unpaid runtime probes should expose a valid `WWW-Authenticate` challenge; the function adds `WWW-Authenticate: x402` alongside the x402 v2 `PAYMENT-REQUIRED` header.
