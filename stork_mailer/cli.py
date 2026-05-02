from __future__ import annotations

from stork_agent.cli import main as agent_main
from stork_agent.connectors.stork_email import StorkEmailConnector
from stork_agent.config import default_profile


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        import sys

        argv = sys.argv[1:]
    if not argv or argv[0].startswith("-"):
        argv = ["run-daily", *argv]
    return agent_main(argv)


def collect_stork_items(args):
    connector = StorkEmailConnector()
    return connector.fetch(default_profile(), since=__import__("datetime").date.today(), limit=getattr(args, "limit", 10))


if __name__ == "__main__":
    raise SystemExit(main())
