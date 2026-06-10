const owner = "asobel12321";
const repo = "incomeforeveryone";
const dailyLaborWorkflow = "daily-labor-watch.yml";
const dailyXWorkflow = "daily-x-post.yml";

function todayInNewYork() {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());

  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

async function dispatchWorkflow(workflow, label) {
  const token = process.env.GITHUB_WORKFLOW_TOKEN;

  if (!token) {
    throw new Error("Missing GITHUB_WORKFLOW_TOKEN environment variable.");
  }

  const date = todayInNewYork();
  const response = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`,
    {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token.trim()}`,
        "Content-Type": "application/json",
        "User-Agent": "incomeforeveryone-netlify-scheduler",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({
        ref: "main",
        inputs: { date },
      }),
    },
  );

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`GitHub dispatch failed (${response.status}): ${detail}`);
  }

  console.log(`${label} dispatched ${workflow} for ${date}`);

  return new Response(JSON.stringify({ ok: true, date, label, workflow }), {
    headers: { "Content-Type": "application/json" },
  });
}

export async function dispatchDailyLaborWatch(label) {
  return dispatchWorkflow(dailyLaborWorkflow, label);
}

export async function dispatchDailyXPost(label) {
  return dispatchWorkflow(dailyXWorkflow, label);
}
