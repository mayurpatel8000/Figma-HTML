from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .agent import FigmaFinalAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert one Figma URL into a standalone HTML/CSS/JS project.")
    parser.add_argument("--figma-url", required=True, help="Figma file/design URL")
    parser.add_argument("--token", default=os.getenv("FIGMA_TOKEN", ""), help="Figma API token or FIGMA_TOKEN")
    parser.add_argument("--output", default="./projects", help="Root folder for generated projects")
    parser.add_argument("--max-iterations", type=int, default=3, help="ReAct loop iteration cap")
    parser.add_argument("--no-approval", action="store_true", help="Skip human approval gate for tests/local automation")
    parser.add_argument("--existing-file", default=None, help="Optional existing code file to read into context")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.token:
        raise SystemExit("A Figma token is required via --token or FIGMA_TOKEN.")

    agent = FigmaFinalAgent(max_iterations=args.max_iterations)
    result = agent.run(
        figma_url=args.figma_url,
        token=args.token,
        output_root=Path(args.output),
        require_approval=not args.no_approval,
        existing_file=args.existing_file,
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    if not result.success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

