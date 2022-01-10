
from textgrid_tools.core.interval_format import (IntervalFormat,
                                                 split_interval_symbols)


def test_empty_input():
  res = list(split_interval_symbols(tuple(), IntervalFormat.WORDS,
                                    join_symbols=None, ignore_join_symbols=None))

  assert res == []
