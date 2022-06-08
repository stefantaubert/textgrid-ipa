from argparse import ArgumentTypeError

import pytest

from textgrid_tools_cli.helper import parse_float


def test_empty__raises_error():
  with pytest.raises(ArgumentTypeError) as ex:
    parse_float("")


def test_None__raises_error():
  with pytest.raises(ArgumentTypeError) as ex:
    parse_float(None)


def test_char__raises_error():
  with pytest.raises(ArgumentTypeError) as ex:
    parse_float("a")


def test_number__is_returned():
  assert parse_float("1") == 1.0


def test_decimalnumber__is_returned():
  assert parse_float("0.5") == 0.5
