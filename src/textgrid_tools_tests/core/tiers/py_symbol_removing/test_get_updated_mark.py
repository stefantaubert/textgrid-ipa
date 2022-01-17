
from text_utils import StringFormat
from textgrid_tools.core.tiers.symbol_removing import get_updated_mark


def test_empty__returns_empty():
  result = get_updated_mark("", StringFormat.TEXT, {}, {}, {})
  assert result == ""


def test_double_hypen__ignore_hypen_returns_empty():
  result = get_updated_mark("- -", StringFormat.SYMBOLS, {}, {"-"}, {})
  assert result == ""
