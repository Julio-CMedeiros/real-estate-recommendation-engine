"""CLI entry point for the recommendation engine."""

import argparse
import json

from .database import get_connection
from .engine.runner import run_engine


def main():
    parser = argparse.ArgumentParser(description="Real Estate Recommendation Engine")
    parser.add_argument("--property-id", type=int, help="Run for a specific property only")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate rules without persisting")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    conn = get_connection()
    recommendations = run_engine(conn, property_id=args.property_id, dry_run=args.dry_run)

    if args.json:
        print(json.dumps([r.to_dict() for r in recommendations], indent=2))
    else:
        if not recommendations:
            print("No recommendations generated.")
            return

        print(f"\n{'='*60}")
        print(f"  Generated {len(recommendations)} recommendation(s)")
        print(f"{'='*60}\n")

        for rec in recommendations:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.priority, "⚪")
            print(f"  {priority_icon} [{rec.code}] {rec.title}")
            print(f"     Type: {rec.type} | Priority: {rec.priority} | Property #{rec.property_id}")
            print(f"     {rec.description}")
            if rec.metadata:
                print(f"     Metadata: {json.dumps(rec.metadata)}")
            print()


if __name__ == "__main__":
    main()
