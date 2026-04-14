from __future__ import annotations

import argparse

from .evaluate import add_evaluate_subparser
from .train import add_train_subparser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Experimental DQN module for SUMO traffic signal control."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_train_subparser(subparsers)
    add_evaluate_subparser(subparsers)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
