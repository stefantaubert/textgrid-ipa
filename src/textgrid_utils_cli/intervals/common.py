from argparse import ArgumentParser


def add_join_with_argument(parser: ArgumentParser) -> None:
  parser.add_argument('--join-with', type=str, metavar="SYMBOL",
                      help="use this symbol as join symbol between the intervals", default=" ")


def add_join_empty_argument(parser: ArgumentParser) -> None:
  parser.add_argument("--join-empty", action="store_true",
                      help="join empty intervals, e.g., `a||b` and join-with `X` -> `aXXb` instead of `aXb`")
