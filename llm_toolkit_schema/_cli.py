"""Command-line interface for llm-toolkit-schema utilities.

This module provides the ``llm-toolkit-schema`` entry-point command.  It is excluded
from coverage measurement because it is a thin integration shim over the
public library API — all business logic lives in tested library modules.

Entry-point (configured in pyproject.toml)::

    llm-toolkit-schema = "llm_toolkit_schema._cli:main"

Sub-commands
------------
``llm-toolkit-schema check-compat <events.json>``
    Load a JSON file containing a list of serialised events and run the
    v1.0 compatibility checklist.  Exits with status 0 on success, 1 on
    violations, and 2 on usage/parse errors.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn


def _cmd_check_compat(args: argparse.Namespace) -> int:
    """Implement the ``check-compat`` sub-command."""
    from llm_toolkit_schema.compliance import test_compatibility
    from llm_toolkit_schema.event import Event

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {path}: {exc}", file=sys.stderr)
        return 2

    if not isinstance(raw, list):
        print("error: JSON file must contain a top-level array of events", file=sys.stderr)
        return 2

    try:
        events = [Event.from_dict(item) for item in raw]
    except Exception as exc:
        print(f"error: could not deserialise events: {exc}", file=sys.stderr)
        return 2

    result = test_compatibility(events)

    if result.passed:
        print(
            f"OK — {result.events_checked} event(s) passed all compatibility checks."
        )
        return 0

    print(
        f"FAIL — {len(result.violations)} violation(s) found in "
        f"{result.events_checked} event(s):\n"
    )
    for v in result.violations:
        event_ref = f"[{v.event_id}] " if v.event_id else ""
        print(f"  {event_ref}{v.check_id} ({v.rule}): {v.detail}")

    return 1


def main(argv: list[str] | None = None) -> NoReturn:
    """Entry point for the ``llm-toolkit-schema`` CLI tool."""
    parser = argparse.ArgumentParser(
        prog="llm-toolkit-schema",
        description="llm-toolkit-schema command-line utilities",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # check-compat sub-command
    compat_parser = sub.add_parser(
        "check-compat",
        help="Check a JSON file of events against the v1.0 compatibility checklist",
    )
    compat_parser.add_argument(
        "file",
        metavar="EVENTS_JSON",
        help="Path to a JSON file containing a list of serialised events",
    )

    args = parser.parse_args(argv)

    if args.command == "check-compat":
        sys.exit(_cmd_check_compat(args))
    else:
        parser.print_help()
        sys.exit(2)
