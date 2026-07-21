#!/usr/bin/env python3
"""Refresh labor statistics from public FRED CSV feeds."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "labor_stats.json"
HISTORY_DATA_PATH = REPO_ROOT / "data" / "labor_stats_history.json"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd=2025-01-01"
HISTORY_OBSERVATION_LIMIT = 13


@dataclass(frozen=True)
class IndicatorDefinition:
    id: str
    label: str
    unit: str
    series_id: str
    source_name: str
    source_url: str
    release_url: str
    status_mode: str
    up_template: str
    down_template: str
    steady_template: str


INDICATORS: tuple[IndicatorDefinition, ...] = (
    IndicatorDefinition(
        id="unemployment-rate",
        label="Unemployment rate",
        unit="percent",
        series_id="UNRATE",
        source_name="U.S. Bureau of Labor Statistics via FRED",
        source_url="https://fred.stlouisfed.org/series/UNRATE",
        release_url="https://www.bls.gov/news.release/empsit.nr0.htm",
        status_mode="lower_is_better",
        up_template="Headline unemployment rose to {value_display}, a weaker signal for worker security.",
        down_template="Headline unemployment fell to {value_display}, keeping the labor market tighter.",
        steady_template="Headline unemployment held at {value_display}, keeping the labor market near its recent range.",
    ),
    IndicatorDefinition(
        id="labor-force-participation",
        label="Labor force participation",
        unit="percent",
        series_id="CIVPART",
        source_name="U.S. Bureau of Labor Statistics via FRED",
        source_url="https://fred.stlouisfed.org/series/CIVPART",
        release_url="https://www.bls.gov/news.release/empsit.nr0.htm",
        status_mode="higher_is_better",
        up_template="Participation rose to {value_display}, improving worker availability.",
        down_template="Participation fell to {value_display}, tightening worker availability.",
        steady_template="Participation was unchanged at {value_display}, leaving worker availability broadly steady.",
    ),
    IndicatorDefinition(
        id="payroll-employment",
        label="Total nonfarm payrolls",
        unit="thousand jobs",
        series_id="PAYEMS",
        source_name="U.S. Bureau of Labor Statistics via FRED",
        source_url="https://fred.stlouisfed.org/series/PAYEMS",
        release_url="https://www.bls.gov/news.release/empsit.nr0.htm",
        status_mode="higher_is_better",
        up_template="Payroll employment increased by {change_abs} thousand to {value_display}, a positive hiring signal.",
        down_template="Payroll employment declined by {change_abs} thousand to {value_display}, a weaker hiring signal.",
        steady_template="Payroll employment was essentially unchanged at {value_display}.",
    ),
    IndicatorDefinition(
        id="job-openings",
        label="Job openings",
        unit="thousand openings",
        series_id="JTSJOL",
        source_name="U.S. Bureau of Labor Statistics via FRED",
        source_url="https://fred.stlouisfed.org/series/JTSJOL",
        release_url="https://www.bls.gov/news.release/jolts.nr0.htm",
        status_mode="higher_is_better",
        up_template="Openings rose by {change_abs} thousand to {value_display}, a labor-demand signal to compare with hiring and quits.",
        down_template="Openings fell by {change_abs} thousand to {value_display}, pointing to softer unmet labor demand.",
        steady_template="Openings were essentially unchanged at {value_display}.",
    ),
    IndicatorDefinition(
        id="u6-underemployment",
        label="U-6 labor underutilization",
        unit="percent",
        series_id="U6RATE",
        source_name="U.S. Bureau of Labor Statistics via FRED",
        source_url="https://fred.stlouisfed.org/series/U6RATE",
        release_url="https://www.bls.gov/news.release/empsit.nr0.htm",
        status_mode="lower_is_better",
        up_template="Broader labor underutilization rose to {value_display}, capturing slack beyond the headline unemployment rate.",
        down_template="Broader labor underutilization eased to {value_display}, but still captures marginal attachment and involuntary part-time work.",
        steady_template="Broader labor underutilization was unchanged at {value_display}.",
    ),
    IndicatorDefinition(
        id="production-wages",
        label="Production and nonsupervisory hourly earnings",
        unit="dollars per hour",
        series_id="AHETPI",
        source_name="U.S. Bureau of Labor Statistics via FRED",
        source_url="https://fred.stlouisfed.org/series/AHETPI",
        release_url="https://www.bls.gov/news.release/empsit.nr0.htm",
        status_mode="higher_is_better",
        up_template="Hourly pay for production and nonsupervisory workers rose to {value_display}, a worker-pay gauge to read alongside inflation and hours.",
        down_template="Hourly pay for production and nonsupervisory workers fell to {value_display}, a weaker worker-pay signal.",
        steady_template="Hourly pay for production and nonsupervisory workers was unchanged at {value_display}.",
    ),
)


def fetch_csv(series_id: str) -> str:
    url = FRED_CSV_URL.format(series_id=series_id)
    last_error: Exception | None = None

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read().decode("utf-8-sig")
        except (ConnectionResetError, TimeoutError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 * attempt)

    raise RuntimeError(f"Could not fetch {series_id} from FRED after 3 attempts: {last_error}")


def parse_observations(series_id: str, csv_text: str) -> list[tuple[date, Decimal]]:
    reader = csv.DictReader(StringIO(csv_text))
    observations: list[tuple[date, Decimal]] = []

    for row in reader:
        raw_date = row.get("observation_date")
        raw_value = row.get(series_id)
        if not raw_date or not raw_value or raw_value == ".":
            continue
        try:
            period = datetime.strptime(raw_date, "%Y-%m-%d").date()
            value = Decimal(raw_value)
        except (ValueError, InvalidOperation):
            continue
        observations.append((period, value))

    if len(observations) < 2:
        raise RuntimeError(f"Expected at least two observations for {series_id}.")

    return observations


def format_period(period: date) -> str:
    return f"{period.strftime('%B')} {period.year}"


def format_value(value: Decimal, unit: str) -> str:
    if unit.startswith("dollars"):
        return f"${value.quantize(Decimal('0.01'))}"
    if unit.startswith("thousand"):
        return f"{int(value):,}"
    return f"{value.normalize():f}"


def status_for(definition: IndicatorDefinition, current: Decimal, previous: Decimal) -> str:
    if current == previous:
        return "steady"
    rose = current > previous
    if definition.status_mode == "lower_is_better":
        return "down" if not rose else "up"
    return "up" if rose else "down"


def build_interpretation(
    definition: IndicatorDefinition,
    value_display: str,
    current: Decimal,
    previous: Decimal,
    status: str,
) -> str:
    change_abs = abs(current - previous)
    if definition.unit.startswith("thousand"):
        change_display = f"{int(change_abs):,}"
    elif definition.unit.startswith("dollars"):
        change_display = f"${change_abs.quantize(Decimal('0.01'))}"
    else:
        change_display = f"{change_abs.normalize():f} percentage points"

    template = {
        "up": definition.up_template,
        "down": definition.down_template,
        "steady": definition.steady_template,
    }[status]
    return template.format(value_display=value_display, change_abs=change_display)


def build_indicator(definition: IndicatorDefinition) -> dict[str, str]:
    observations = fetch_observations(definition)
    return build_indicator_from_observations(definition, observations)


def fetch_observations(definition: IndicatorDefinition) -> list[tuple[date, Decimal]]:
    return parse_observations(definition.series_id, fetch_csv(definition.series_id))


def build_indicator_from_observations(
    definition: IndicatorDefinition,
    observations: list[tuple[date, Decimal]],
) -> dict[str, str]:
    current_period, current_value = observations[-1]
    _, previous_value = observations[-2]
    value_display = format_value(current_value, definition.unit)
    status = status_for(definition, current_value, previous_value)

    return {
        "id": definition.id,
        "label": definition.label,
        "value": value_display,
        "unit": definition.unit,
        "period": format_period(current_period),
        "frequency": "Monthly",
        "seasonality": "Seasonally adjusted",
        "series_id": definition.series_id,
        "source_name": definition.source_name,
        "source_url": definition.source_url,
        "release_url": definition.release_url,
        "updated": date.today().isoformat(),
        "status": status,
        "interpretation": build_interpretation(definition, value_display, current_value, previous_value, status),
    }


def build_history_observations(
    definition: IndicatorDefinition,
    observations: list[tuple[date, Decimal]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    recent = observations[-HISTORY_OBSERVATION_LIMIT:]

    for index, (period, value) in enumerate(recent):
        previous_value = recent[index - 1][1] if index > 0 else None
        row = {
            "date": period.isoformat(),
            "period": format_period(period),
            "value": format_value(value, definition.unit),
            "raw_value": str(value),
        }

        if previous_value is not None:
            change = value - previous_value
            row["month_over_month_change"] = str(change)
            row["status"] = status_for(definition, value, previous_value)

        rows.append(row)

    return rows


def build_history_payload(snapshot: dict, observations_by_id: dict[str, list[tuple[date, Decimal]]]) -> dict:
    indicators = []
    deltas = []

    for definition in INDICATORS:
        observations = observations_by_id[definition.id]
        current_period, current_value = observations[-1]
        previous_period, previous_value = observations[-2]
        change = current_value - previous_value
        status = status_for(definition, current_value, previous_value)

        indicators.append(
            {
                "id": definition.id,
                "label": definition.label,
                "unit": definition.unit,
                "frequency": "Monthly",
                "seasonality": "Seasonally adjusted",
                "series_id": definition.series_id,
                "source_name": definition.source_name,
                "source_url": definition.source_url,
                "release_url": definition.release_url,
                "observations": build_history_observations(definition, observations),
            }
        )
        deltas.append(
            {
                "id": definition.id,
                "label": definition.label,
                "current_period": format_period(current_period),
                "previous_period": format_period(previous_period),
                "change": str(change),
                "status": status,
            }
        )

    return {
        "schema_version": "2026-07-21",
        "endpoint": "/api/labor-stats/history",
        "snapshot_as_of": snapshot["as_of"],
        "history_window": {
            "frequency": "Monthly",
            "observation_count_per_indicator": HISTORY_OBSERVATION_LIMIT,
            "start_date": min(rows[-HISTORY_OBSERVATION_LIMIT][0] for rows in observations_by_id.values()).isoformat(),
            "end_date": max(rows[-1][0] for rows in observations_by_id.values()).isoformat(),
        },
        "indicators": indicators,
        "revisions": [],
        "deltas": deltas,
        "sources": snapshot["sources"],
        "access": {
            "tier": "premium",
            "payment_required": True,
            "payment_protocol": "x402",
            "public_fallback": "/api/labor-stats/",
        },
    }


def load_existing(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse existing data file {path}: {exc}") from exc


def merge_existing_metadata(indicators: list[dict[str, str]], existing: dict) -> tuple[list[dict[str, str]], bool]:
    existing_by_id = {
        indicator.get("id"): indicator
        for indicator in existing.get("indicators", [])
        if isinstance(indicator, dict) and indicator.get("id")
    }
    changed = False

    for indicator in indicators:
        old = existing_by_id.get(indicator["id"])
        if not old:
            changed = True
            continue

        value_changed = (
            old.get("value") != indicator.get("value")
            or old.get("period") != indicator.get("period")
            or old.get("status") != indicator.get("status")
        )
        if value_changed:
            changed = True
            continue

        indicator["updated"] = old.get("updated", indicator["updated"])
        indicator["interpretation"] = old.get("interpretation", indicator["interpretation"])

    if len(existing_by_id) != len(indicators):
        changed = True

    return indicators, changed


def build_payload(existing: dict) -> tuple[dict, dict]:
    observations_by_id = {definition.id: fetch_observations(definition) for definition in INDICATORS}
    indicators, indicators_changed = merge_existing_metadata(
        [
            build_indicator_from_observations(definition, observations_by_id[definition.id])
            for definition in INDICATORS
        ],
        existing,
    )
    today = date.today().isoformat()
    as_of = today if indicators_changed else existing.get("as_of", today)
    release_context = existing.get("release_context", {})
    as_of_date = datetime.strptime(as_of, "%Y-%m-%d").date()

    snapshot = {
        "as_of": as_of,
        "coverage": "United States",
        "release_context": {
            "label": (
                "Latest monthly labor-market releases available as of "
                f"{as_of_date.strftime('%B')} {as_of_date.day}, {as_of_date.year}"
            ),
            "next_employment_release": release_context.get("next_employment_release", ""),
            "next_jolts_release": release_context.get("next_jolts_release", ""),
            "note": "Values are public, seasonally adjusted headline indicators from BLS series as displayed by FRED. Data may be revised.",
        },
        "indicators": indicators,
        "sources": [
            {
                "name": "BLS Employment Situation",
                "url": "https://www.bls.gov/news.release/empsit.nr0.htm",
                "last_checked": date.today().isoformat(),
            },
            {
                "name": "BLS Job Openings and Labor Turnover Survey",
                "url": "https://www.bls.gov/news.release/jolts.nr0.htm",
                "last_checked": date.today().isoformat(),
            },
            {
                "name": "FRED labor-market series pages",
                "url": "https://fred.stlouisfed.org/",
                "last_checked": date.today().isoformat(),
            },
        ],
        "future_api": {
            "public_path": "/labor-stats/",
            "candidate_endpoint": "/api/labor-stats",
            "candidate_marketplace": "Merit Systems",
            "payment_protocol": "x402",
            "contract_note": "Keep ids, source fields, periods, units, and release metadata stable before exposing paid agent access.",
        },
    }
    return snapshot, build_history_payload(snapshot, observations_by_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DATA_PATH)
    parser.add_argument("--history-output", type=Path, default=HISTORY_DATA_PATH)
    parser.add_argument("--check", action="store_true", help="Exit nonzero if the output file would change.")
    args = parser.parse_args()

    existing = load_existing(args.output)
    payload, history_payload = build_payload(existing)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    history_rendered = json.dumps(history_payload, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        existing_snapshot = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        existing_history = args.history_output.read_text(encoding="utf-8") if args.history_output.exists() else ""
        stale_paths = [
            str(path)
            for path, existing_text, new_text in (
                (args.output, existing_snapshot, rendered),
                (args.history_output, existing_history, history_rendered),
            )
            if existing_text != new_text
        ]
        if stale_paths:
            print(f"{', '.join(stale_paths)} is not current.", file=sys.stderr)
            return 1
        print(f"{args.output} and {args.history_output} are current.")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    args.history_output.parent.mkdir(parents=True, exist_ok=True)
    args.history_output.write_text(history_rendered, encoding="utf-8", newline="\n")
    print(f"Refreshed {args.output} and {args.history_output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
