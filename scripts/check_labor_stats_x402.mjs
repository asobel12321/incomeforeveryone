import handler from "../netlify/functions/labor-stats-history.mjs";

const route = "https://incomeforeveryone.org/api/labor-stats/history";

function fail(message) {
  throw new Error(message);
}

async function parseJsonResponse(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`Expected JSON response, got: ${text}`, { cause: error });
  }
}

function withTemporaryEnv(values, callback) {
  const previous = {};
  const keys = Object.keys(values);

  for (const key of keys) {
    previous[key] = process.env[key];
    if (values[key] === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = values[key];
    }
  }

  return Promise.resolve()
    .then(callback)
    .finally(() => {
      for (const key of keys) {
        if (previous[key] === undefined) {
          delete process.env[key];
        } else {
          process.env[key] = previous[key];
        }
      }
    });
}

async function checkDisabledPath() {
  await withTemporaryEnv(
    {
      NETLIFY_DEV: undefined,
      X402_LABOR_STATS_DEV_BYPASS: undefined,
      X402_LABOR_STATS_ENABLED: undefined,
      X402_PAY_TO: undefined,
      X402_FACILITATOR_URL: undefined,
    },
    async () => {
      const response = await handler(new Request(route));
      const body = await parseJsonResponse(response);

      if (response.status !== 503) fail(`Disabled path returned ${response.status}, expected 503.`);
      if (body.error !== "premium_route_not_configured") {
        fail(`Disabled path returned ${body.error}, expected premium_route_not_configured.`);
      }
      if (body.endpoint !== "/api/labor-stats/history") {
        fail(`Disabled path returned endpoint ${body.endpoint}.`);
      }
    },
  );
}

async function checkDevBypassPath() {
  await withTemporaryEnv(
    {
      NETLIFY_DEV: "true",
      X402_LABOR_STATS_DEV_BYPASS: undefined,
      X402_LABOR_STATS_ENABLED: undefined,
    },
    async () => {
      const response = await handler(new Request(route));
      const body = await parseJsonResponse(response);

      if (response.status !== 200) fail(`Dev bypass returned ${response.status}, expected 200.`);
      if (body.endpoint !== "/api/labor-stats/history") fail("Dev bypass returned wrong endpoint.");
      if (body.access?.dev_bypass !== true) fail("Dev bypass did not mark access.dev_bypass=true.");
      if (body.access?.payment_verified !== false) {
        fail("Dev bypass should return access.payment_verified=false.");
      }
      if (!Array.isArray(body.indicators) || body.indicators.length !== 6) {
        fail(`Dev bypass returned ${body.indicators?.length ?? "no"} indicators, expected 6.`);
      }
      if (!Array.isArray(body.indicators[0].observations) || body.indicators[0].observations.length !== 13) {
        fail("Dev bypass first indicator should include 13 observations.");
      }
    },
  );
}

async function checkMethodRejection() {
  const response = await handler(new Request(route, { method: "POST" }));
  const body = await parseJsonResponse(response);

  if (response.status !== 405) fail(`POST returned ${response.status}, expected 405.`);
  if (body.error !== "method_not_allowed") fail(`POST returned ${body.error}, expected method_not_allowed.`);
}

async function checkConfiguredChallenge() {
  if (process.env.CHECK_X402_TESTNET_CHALLENGE !== "true") {
    console.log("Skipping configured x402 challenge check; set CHECK_X402_TESTNET_CHALLENGE=true to enable it.");
    return;
  }

  await withTemporaryEnv(
    {
      X402_LABOR_STATS_ENABLED: "true",
      X402_PAY_TO: "0x000000000000000000000000000000000000dEaD",
      X402_FACILITATOR_URL: "https://x402.org/facilitator",
      X402_NETWORK: "eip155:84532",
      X402_ASSET: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
      NETLIFY_DEV: undefined,
      X402_LABOR_STATS_DEV_BYPASS: undefined,
    },
    async () => {
      const response = await handler(
        new Request(route, {
          headers: {
            accept: "application/json",
          },
        }),
      );
      const paymentRequired = response.headers.get("PAYMENT-REQUIRED");

      if (response.status !== 402) fail(`Configured x402 check returned ${response.status}, expected 402.`);
      if (!paymentRequired) fail("Configured x402 check did not return PAYMENT-REQUIRED.");

      const decoded = JSON.parse(Buffer.from(paymentRequired, "base64").toString("utf8"));
      const accept = decoded.accepts?.[0];

      if (decoded.x402Version !== 2) fail(`Expected x402Version 2, got ${decoded.x402Version}.`);
      if (decoded.resource?.url !== route) fail(`Expected resource ${route}, got ${decoded.resource?.url}.`);
      if (accept?.network !== "eip155:84532") fail(`Expected eip155:84532, got ${accept?.network}.`);
      if (accept?.amount !== "10000") fail(`Expected amount 10000, got ${accept?.amount}.`);
      if (accept?.asset !== "0x036CbD53842c5426634e7929541eC2318f3dCF7e") {
        fail(`Unexpected asset ${accept?.asset}.`);
      }
    },
  );
}

await checkDisabledPath();
await checkDevBypassPath();
await checkMethodRejection();
await checkConfiguredChallenge();

console.log("labor stats x402 checks passed");
