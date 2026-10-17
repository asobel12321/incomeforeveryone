"""Parse generated feeds and JSON so successful Hugo builds cannot hide malformed output."""

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def check_site(directory: Path) -> None:
    api_paths = [directory / "api" / route / "index.html" for route in ("latest", "articles", "labor-stats")]
    for required in ("ai-jobs-brief.xml", "posts/index.xml", "feed.json", "api/latest/index.html", "api/articles/index.html", "api/labor-stats/index.html", "openapi.json"):
        if not (directory / required).is_file():
            raise ValueError(f"Missing generated interface: {required}")
    paths = sorted([*directory.rglob("*.xml"), *directory.rglob("*.json"), *api_paths])
    for path in paths:
        try:
            if path.suffix == ".xml":
                ET.parse(path)
            else:
                json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, ET.ParseError) as exc:
            raise ValueError(f"Malformed generated interface {path}: {exc}") from exc
    print(f"Parsed {len(paths)} XML/JSON interfaces.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, required=True)
    check_site(parser.parse_args().site_dir)
