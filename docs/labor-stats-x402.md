# Labor history API operations

## Deployed contract

- Free: `/labor-stats/` and `/api/labor-stats/` expose the latest sourced snapshot.
- Paid: `/api/labor-stats/history`, $0.01 per successful request, Base USDC (`eip155:8453`).
- Payload: up to 13 recent monthly observations per indicator, values, monthly changes, latest deltas, and source/access metadata. Inclusive `from`/`to` date filters are supported; invalid or empty ranges fail before payment.
- `revisions` is reserved and empty. Longer history, derived metrics, and composite indexes are parked, not deployed.
- `static/openapi.json` is the single contract source, published at `/openapi.json`. The legacy `listing.openapi_draft` metadata key points there for compatibility; there is no duplicate draft file.
- Production configuration and x402scan registration were completed in July 2026; do not repeat setup as an unfinished launch task.

## Runtime and configuration

`netlify/functions/labor-stats-history.mjs` uses the x402 SDK to challenge, verify, settle, and return `PAYMENT-RESPONSE`. No production premium response may bypass successful verification and settlement.

Required Netlify settings: `X402_LABOR_STATS_ENABLED=true`, `X402_PAY_TO`, and `X402_FACILITATOR_URL`. The established facilitator is PayAI. Missing/disabled configuration must not expose premium data.

Optional overrides: `X402_NETWORK`, `X402_ASSET`, `X402_AMOUNT_ATOMIC` (default 10000), `X402_ASSET_NAME`, `X402_ASSET_VERSION`. Defaults target Base USDC. Facilitator authentication, if required, uses `X402_FACILITATOR_AUTH_HEADER_NAME` and `X402_FACILITATOR_AUTH_HEADER_VALUE` only in Netlify settings. Keep credentials out of source and logs.

Local/dev bypass exists for payload testing and is rejected in production. Preserve that boundary.

## Refresh and verification

```powershell
python -m py_compile scripts/refresh_labor_stats.py
python scripts/refresh_labor_stats.py
python scripts/refresh_labor_stats.py --check
npm.cmd run check:functions
npm.cmd run check:x402
hugo --destination "$env:TEMP/ife-hugo-check"
```

For verification without changing checked-in data, supply temporary `--output` and `--history-output` paths to both refresher invocations. Network access to FRED is required. The npm x402 check is offline unless `CHECK_X402_TESTNET_CHALLENGE=true` is explicitly enabled. An unpaid 402 or testnet challenge proves neither paid production fulfillment nor ordinary-client compatibility.

## Known verification gap

July records show a real production payment returning HTTP 200, premium JSON, and PAYMENT-RESPONSE after removing the optional Bazaar extension from the client-generated payment. Ordinary AgentCash fetch returned another 402. Current normal-client behavior and the newer filtered paid response still need a controlled paid test. Do not describe payment as never tested, claim that this old failure remains current without testing, or remove verification/security controls to work around it.
