from argparse import ArgumentTypeError

import pytest

from textgrid_tools_cli.helper import parse_codec


def test_empty__raises_error():
  with pytest.raises(ArgumentTypeError) as ex:
    parse_codec("")


def test_None__raises_error():
  with pytest.raises(ArgumentTypeError) as ex:
    parse_codec(None)


def test_invalid_code__raises_error():
  with pytest.raises(ArgumentTypeError) as ex:
    parse_codec("abcd")


def test_ascii__returns_ascii():
  assert parse_codec("ascii") == "ascii"


def test_utf_8__returns_utf_8():
  assert parse_codec("utf-8") == "utf-8"
