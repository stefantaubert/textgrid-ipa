
from textgrid_utils.interval_format import (IntervalFormat,
                                            split_interval_symbols)


def test_empty_input():
  res = list(split_interval_symbols(tuple(), IntervalFormat.WORDS,
                                    join_symbols=None, ignore_join_symbols=None))

  assert res == []


def test_one_space():
  res = list(split_interval_symbols(("Is right"), IntervalFormat.WORDS,
                                    join_symbols=None, ignore_join_symbols=None))

  assert res == [('I', 's'), ('r', 'i', 'g', 'h', 't')]


def test_double_space__is_ignored():
  res = list(split_interval_symbols(("Is  right"), IntervalFormat.WORDS,
                                    join_symbols=None, ignore_join_symbols=None))

  assert res == [('I', 's'), ('r', 'i', 'g', 'h', 't')]
