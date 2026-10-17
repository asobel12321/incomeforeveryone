"""Wait for an edition to be deployed before publishing its link externally."""

import argparse
import time
from datetime import date

from check_publication_health import BASE_URL, fetch_bytes, parse_date


def wait_for_article(day: date, *, attempts: int = 20, delay: int = 30) -> None:
    url = f"{BASE_URL}/posts/{day.isoformat()}/"
    for attempt in range(attempts):
        try:
            fetch_bytes(url, {"text/html"})
            print(f"Deployed article available: {url}")
            return
        except (OSError, ValueError) as exc:
            if attempt == attempts - 1:
                raise RuntimeError(f"Article is not deployed: {url}") from exc
            print(f"Waiting for deployment ({attempt + 1}/{attempts}): {exc}", flush=True)
            time.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=parse_date, required=True)
    wait_for_article(parser.parse_args().date)
