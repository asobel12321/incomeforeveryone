import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { x402HTTPResourceServer } from "@x402/core/http";
import { HTTPFacilitatorClient, x402ResourceServer } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";

const ACCESS_CONTROL = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
};

const BASE_MAINNET = "eip155:8453";
const BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";
const DEFAULT_AMOUNT_ATOMIC = "10000";
const premiumRoute = "/api/labor-stats/history";

function jsonResponse(status, body, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...ACCESS_CONTROL,
      ...headers,
    },
  });
}

function x402Config() {
  const network = process.env.X402_NETWORK || BASE_MAINNET;
  const asset = process.env.X402_ASSET || (network === BASE_MAINNET ? BASE_USDC : "");
  const facilitatorAuthHeaderName = process.env.X402_FACILITATOR_AUTH_HEADER_NAME;
  const facilitatorAuthHeaderValue = process.env.X402_FACILITATOR_AUTH_HEADER_VALUE;

  return {
    enabled: process.env.X402_LABOR_STATS_ENABLED === "true",
    payTo: process.env.X402_PAY_TO,
    network,
    asset,
    amountAtomic: process.env.X402_AMOUNT_ATOMIC || DEFAULT_AMOUNT_ATOMIC,
    facilitatorUrl: process.env.X402_FACILITATOR_URL,
    facilitatorAuthHeaderName,
    facilitatorAuthHeaderValue,
  };
}

function missingConfig(config) {
  return Object.entries(config)
    .filter(
      ([key, value]) =>
        ![
          "enabled",
          "amountAtomic",
          "facilitatorAuthHeaderName",
          "facilitatorAuthHeaderValue",
        ].includes(key) && !value,
    )
    .map(([key]) => key);
}

function facilitatorAuthConfigured(config) {
  return Boolean(config.facilitatorAuthHeaderName && config.facilitatorAuthHeaderValue);
}

async function facilitatorAuthHeaders(config) {
  if (!facilitatorAuthConfigured(config)) {
    return {
      verify: {},
      settle: {},
      supported: {},
    };
  }

  const headers = {
    [config.facilitatorAuthHeaderName]: config.facilitatorAuthHeaderValue,
  };

  return {
    verify: headers,
    settle: headers,
    supported: headers,
    bazaar: headers,
  };
}

function devBypassEnabled() {
  if (process.env.CONTEXT === "production") return false;
  return (
    process.env.NETLIFY_DEV === "true" ||
    (process.env.X402_LABOR_STATS_DEV_BYPASS === "true" && process.env.CONTEXT !== "production")
  );
}

async function loadHistoryPayload() {
  const raw = await readFile(join(process.cwd(), "data", "labor_stats_history.json"), "utf8");
  return JSON.parse(raw);
}

function readDateRange(request) {
  const params = new URL(request.url).searchParams;
  for (const key of params.keys()) {
    if (!["from", "to"].includes(key) || params.getAll(key).length !== 1) {
      throw new RangeError("Use only one from and one to parameter.");
    }
  }
  const range = { from: params.get("from"), to: params.get("to") };
  for (const value of Object.values(range)) {
    if (value === null) continue;
    const parsed = new Date(`${value}T00:00:00Z`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(parsed.getTime()) ||
        parsed.toISOString().slice(0, 10) !== value) {
      throw new RangeError("Dates must be valid YYYY-MM-DD calendar dates.");
    }
  }
  if (range.from && range.to && range.from > range.to) {
    throw new RangeError("from must be on or before to.");
  }
  return range;
}

function filterHistory(payload, range) {
  if (!range.from && !range.to) return payload;
  const indicators = payload.indicators.map((indicator) => {
    const observations = indicator.observations
      .filter((row) => (!range.from || row.date >= range.from) && (!range.to || row.date <= range.to))
      .map((row) => ({ ...row }));
    // The first returned month has no preceding observation within this range.
    if (observations.length) {
      delete observations[0].month_over_month_change;
      delete observations[0].status;
    }
    return { ...indicator, observations };
  });
  const dates = indicators.flatMap((indicator) => indicator.observations.map((row) => row.date)).sort();
  if (!dates.length) throw new RangeError("No observations are available in the requested range.");
  const deltas = indicators.filter((indicator) => indicator.observations.length >= 2).map((indicator) => {
    const current = indicator.observations.at(-1);
    const previous = indicator.observations.at(-2);
    return {
      id: indicator.id,
      label: indicator.label,
      current_period: current.period,
      previous_period: previous.period,
      change: current.month_over_month_change,
      status: current.status,
    };
  });
  return {
    ...payload,
    indicators,
    deltas,
    history_window: {
      ...payload.history_window,
      observation_count_per_indicator: Math.max(...indicators.map((indicator) => indicator.observations.length)),
      start_date: dates[0],
      end_date: dates.at(-1),
    },
  };
}

function createAdapter(request) {
  const url = new URL(request.url);

  return {
    getHeader(name) {
      return request.headers.get(name) || undefined;
    },
    getMethod() {
      return request.method;
    },
    getPath() {
      return url.pathname;
    },
    getUrl() {
      return request.url;
    },
    getAcceptHeader() {
      return request.headers.get("accept") || "";
    },
    getUserAgent() {
      return request.headers.get("user-agent") || "";
    },
    getQueryParams() {
      const params = {};
      for (const [key, value] of url.searchParams.entries()) {
        if (params[key] === undefined) {
          params[key] = value;
        } else if (Array.isArray(params[key])) {
          params[key].push(value);
        } else {
          params[key] = [params[key], value];
        }
      }
      return params;
    },
    getQueryParam(name) {
      const values = url.searchParams.getAll(name);
      if (values.length === 0) return undefined;
      return values.length === 1 ? values[0] : values;
    },
  };
}

function responseFromInstructions(instructions) {
  const body =
    instructions.body === undefined
      ? undefined
      : instructions.isHtml
        ? String(instructions.body)
        : JSON.stringify(instructions.body);
  const headers = new Headers(instructions.headers);

  if (instructions.status === 402 && headers.has("PAYMENT-REQUIRED") && !headers.has("WWW-Authenticate")) {
    headers.set("WWW-Authenticate", "x402");
  }

  return new Response(body, {
    status: instructions.status,
    headers,
  });
}

function x402Price(config) {
  return {
    asset: config.asset,
    amount: config.amountAtomic,
    extra: {
      name: process.env.X402_ASSET_NAME || "USD Coin",
      version: process.env.X402_ASSET_VERSION || "2",
    },
  };
}

function bazaarDiscoveryExtension() {
  return {
    input: {
      queryParams: {
        from: "2025-07-01",
        to: "2026-07-01",
      },
    },
    schema: {
      type: "object",
      properties: {
        input: {
          type: "object",
          properties: {
            queryParams: {
              type: "object",
              properties: {
                from: {
                  type: "string",
                  format: "date",
                  description: "Optional inclusive start date for historical observations.",
                },
                to: {
                  type: "string",
                  format: "date",
                  description: "Optional inclusive end date for historical observations.",
                },
              },
              additionalProperties: false,
            },
          },
          required: ["queryParams"],
          additionalProperties: false,
        },
        output: {
          type: "object",
          properties: {
            example: {
              type: "object",
              properties: {
                schema_version: { type: "string" },
                endpoint: { type: "string", const: premiumRoute },
                snapshot_as_of: { type: "string", format: "date" },
                history_window: {
                  type: "object",
                  properties: {
                    frequency: { type: "string" },
                    observation_count_per_indicator: { type: "integer" },
                    start_date: { type: "string", format: "date" },
                    end_date: { type: "string", format: "date" },
                  },
                  required: ["frequency", "observation_count_per_indicator", "start_date", "end_date"],
                },
                indicators: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      id: { type: "string" },
                      label: { type: "string" },
                      unit: { type: "string" },
                      series_id: { type: "string" },
                      observations: {
                        type: "array",
                        items: {
                          type: "object",
                          properties: {
                            date: { type: "string", format: "date" },
                            period: { type: "string" },
                            value: { type: "string" },
                            raw_value: { type: "string" },
                            month_over_month_change: { type: "string" },
                          },
                          required: ["date", "period", "value", "raw_value"],
                        },
                      },
                    },
                    required: ["id", "label", "unit", "series_id", "observations"],
                  },
                },
                deltas: { type: "array", items: { type: "object" } },
                sources: { type: "array", items: { type: "object" } },
                access: { type: "object" },
              },
              required: [
                "schema_version",
                "endpoint",
                "snapshot_as_of",
                "history_window",
                "indicators",
                "sources",
                "access",
              ],
            },
          },
          required: ["example"],
          additionalProperties: false,
        },
      },
      required: ["input", "output"],
    },
  };
}

let cachedServerKey;
let cachedServerPromise;

async function getPaymentServer(config) {
  const serverKey = JSON.stringify({
    facilitatorUrl: config.facilitatorUrl,
    network: config.network,
    payTo: config.payTo,
    asset: config.asset,
    amountAtomic: config.amountAtomic,
  });

  if (cachedServerKey === serverKey && cachedServerPromise) {
    return cachedServerPromise;
  }

  cachedServerKey = serverKey;
  cachedServerPromise = (async () => {
    const facilitatorClient = new HTTPFacilitatorClient({
      url: config.facilitatorUrl,
      createAuthHeaders: () => facilitatorAuthHeaders(config),
    });
    const resourceServer = new x402ResourceServer(facilitatorClient).register(
      config.network,
      new ExactEvmScheme(),
    );
    const httpServer = new x402HTTPResourceServer(resourceServer, {
      [`GET ${premiumRoute}`]: {
        accepts: [
          {
            scheme: "exact",
            price: x402Price(config),
            network: config.network,
            payTo: config.payTo,
            maxTimeoutSeconds: 300,
          },
        ],
        description:
          "Recent monthly labor-market observations, month-over-month changes, and source metadata.",
        mimeType: "application/json",
        resource: `https://incomeforeveryone.org${premiumRoute}`,
        serviceName: "Income For Everyone Labor Stats History API",
        tags: ["labor", "economics", "automation", "analytics"],
        extensions: {
          bazaar: bazaarDiscoveryExtension(),
        },
      },
    });

    await httpServer.initialize();
    return httpServer;
  })();

  return cachedServerPromise;
}

export default async (request) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    return jsonResponse(405, {
      error: "method_not_allowed",
      allowed_methods: ["GET", "HEAD"],
    });
  }

  const config = x402Config();
  const missing = missingConfig(config);
  const devBypass = devBypassEnabled();

  if (!devBypass && (!config.enabled || missing.length > 0)) {
    return jsonResponse(503, {
      error: "premium_route_not_configured",
      endpoint: premiumRoute,
      status: "disabled",
      payment_protocol: "x402",
      required_configuration: [
        "X402_LABOR_STATS_ENABLED=true",
        "X402_PAY_TO",
        "X402_FACILITATOR_URL",
      ],
      optional_configuration: [
        "X402_NETWORK defaults to eip155:8453",
        "X402_ASSET defaults to Base USDC on eip155:8453",
        "X402_AMOUNT_ATOMIC defaults to 10000 ($0.01 USDC)",
      ],
      missing_configuration: config.enabled ? missing : ["enabled"],
      public_fallback: "/api/labor-stats/",
    });
  }

  let payload;
  try {
    const range = readDateRange(request);
    payload = filterHistory(await loadHistoryPayload(), range);
  } catch (error) {
    if (error instanceof RangeError) {
      return jsonResponse(400, { error: "invalid_date_range", detail: error.message });
    }
    return jsonResponse(503, { error: "history_unavailable", public_fallback: "/api/labor-stats/" });
  }

  if (devBypass) {
    return jsonResponse(200, {
      ...payload,
      access: {
        ...payload.access,
        dev_bypass: true,
        payment_verified: false,
        warning: "Local/dev bypass only. Production must verify and settle x402 payment before fulfillment.",
      },
    });
  }

  let paymentServer;
  try {
    paymentServer = await getPaymentServer(config);
  } catch (error) {
    return jsonResponse(503, {
      error: "x402_initialization_failed",
      endpoint: premiumRoute,
      detail: error instanceof Error ? error.message : String(error),
      public_fallback: "/api/labor-stats/",
    });
  }

  const adapter = createAdapter(request);
  const requestContext = {
    adapter,
    path: adapter.getPath(),
    method: adapter.getMethod(),
  };
  const paymentResult = await paymentServer.processHTTPRequest(requestContext);

  if (paymentResult.type === "payment-error") {
    return responseFromInstructions(paymentResult.response);
  }

  if (paymentResult.type !== "payment-verified") {
    return jsonResponse(503, { error: "payment_verification_required" });
  }
  const body = JSON.stringify({
    ...payload,
    access: {
      ...payload.access,
      payment_verified: true,
    },
  });
  const responseHeaders = {
    ...ACCESS_CONTROL,
  };
  const settlement = await paymentServer.processSettlement(
    paymentResult.paymentPayload,
    paymentResult.paymentRequirements,
    paymentResult.declaredExtensions,
    {
      request: requestContext,
      responseBody: Buffer.from(body),
      responseHeaders,
    },
  );

  if (!settlement.success) {
    return responseFromInstructions(settlement.response);
  }

  return new Response(body, {
    status: 200,
    headers: {
      ...responseHeaders,
      ...settlement.headers,
    },
  });
};
