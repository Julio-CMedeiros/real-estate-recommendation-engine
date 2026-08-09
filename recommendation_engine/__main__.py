"""CLI entry point for the recommendation engine."""

import argparse
import json
import sys

from .database import get_connection
from .engine.runner import run_engine


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Real Estate Recommendation Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run recommendation rules")
    run_parser.add_argument("--property-id", type=int, help="Run for a specific property only")
    run_parser.add_argument("--dry-run", action="store_true", help="Evaluate rules without persisting")
    run_parser.add_argument("--json", action="store_true", help="Output as JSON")
    run_parser.add_argument("--db-path", help="Override the database path (mainly for testing)")

    key_parser = subparsers.add_parser("create-key", help="Create a new API key for a consumer service")
    key_parser.add_argument("consumer_name", help="Name of the service that will use this key")
    key_parser.add_argument("--db-path", help="Override the database path (mainly for testing)")

    return parser


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] not in ("run", "create-key"):
        argv = ["run", *argv]

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "create-key":
        _create_key(args.consumer_name, args.db_path)
        return

    _run(args)


def _create_key(consumer_name: str, db_path: str | None) -> None:
    from api.auth import create_api_key

    conn = get_connection(db_path)
    raw_key = create_api_key(conn, consumer_name)
    conn.close()
    print(f"API key created for '{consumer_name}'. Store it now — it will not be shown again:")
    print(raw_key)


def _run(args) -> None:
    conn = get_connection(args.db_path)
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
