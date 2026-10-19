"""Optionally emit MAGNET's native source-to-Lean theory-link report.

Requires full ``aiq-magnet`` (for its static parser and theory index), not just
``aiq-magnet-theory`` (whose decorators are inert at runtime).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "theory" / "link-spec.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "theory" / "report.json")
    args = parser.parse_args()
    try:
        from magnet.theory.cards import report_from_card
    except ImportError as exc:
        parser.error(
            "This optional report requires the full aiq-magnet package "
            "(not only aiq-magnet-theory). Install aiq-magnet in your "
            f"environment. Import error: {exc}"
        )
    spec = yaml.safe_load(SPEC.read_text())
    report = report_from_card(spec, root=SPEC.parent)
    if report is None:
        parser.error("No theory links were found in the specified sources")
    if report.unresolved:
        parser.error(f"Unresolved theory links: {report.unresolved}")
    report.write(args.output)
    data = report.to_dict()
    print(f"Theory report: {args.output}")
    print(f"  statement links: {len(data['statement_links'])}")
    print(f"  premise links:   {len(data['premise_links'])}")
    for item in data['premise_coverage']:
        print(
            f"  {item['ref']}: {item['accounted_count']}/"
            f"{item['premise_count']} premises accounted for"
        )
        if item['unaccounted']:
            print(f"    unaccounted: {', '.join(item['unaccounted'])}")


if __name__ == "__main__":
    main()
