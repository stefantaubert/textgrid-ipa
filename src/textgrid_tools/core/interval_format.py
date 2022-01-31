from enum import IntEnum
from typing import Generator, Iterable, Optional, Set

from text_utils.pronunciation.ipa2symb import merge_left, merge_right
from text_utils.string_format import convert_symbols_string_to_symbols
from text_utils.types import Symbol, Symbols
from text_utils.utils import symbols_join, symbols_split_iterable
from textgrid_tools.core.helper import symbols_are_empty_or_whitespace


class IntervalFormat(IntEnum):
  SYMBOL = 0
  SYMBOLS = 1
  WORD = 2
  WORDS = 3

  def __repr__(self) -> str:
    if self == self.SYMBOL:
      return "Symbol"

    if self == self.SYMBOLS:
      return "Symbols"

    if self == self.WORD:
      return "Word"

    if self == self.WORDS:
      return "Words"

    assert False


def merge_interval_symbols(interval_symbols: Iterable[Symbols], intervals_interval_format: IntervalFormat, join_symbols: Optional[Set[Symbol]], ignore_join_symbols: Optional[Set[Symbol]]) -> Generator[Symbols, None, None]:
  """
  Examples:
  - SYMBOL -> SYMBOLS with join ".": |aa|.| | |b|.|d| -> |aa .|b .|d|
  - SYMBOLS -> WORD: |aa .| | |b .|d| -> |aa . b . d|
  - WORD -> WORDS: |aa b| | |b cc .|d| -> |aa b  b cc .  d|
  """

  non_pause_symbols = (
    symbols
    for symbols in interval_symbols if not symbols_are_empty_or_whitespace(symbols)
  )
  target_format = get_upper_format(intervals_interval_format)
  symbols = list(non_pause_symbols)

  if target_format == IntervalFormat.SYMBOLS:
    if join_symbols is not None:
      ignore_merge_symbols = set()
      if ignore_join_symbols is not None:
        ignore_merge_symbols = ignore_join_symbols

      symbols = merge_right(
        symbols=symbols,
        ignore_merge_symbols=ignore_merge_symbols,
        merge_symbols=join_symbols,
        insert_symbol=" ",
      )

      symbols = merge_left(
        symbols=symbols,
        ignore_merge_symbols=ignore_merge_symbols,
        merge_symbols=join_symbols,
        insert_symbol=" ",
      )

    result = (
      convert_symbols_string_to_symbols(symbol_str)
      for symbol_str in symbols
    )
    return result

  elif target_format == IntervalFormat.WORD:
    yield symbols_join(symbols, join_symbol=None)
  elif target_format == IntervalFormat.WORDS:
    yield symbols_join(symbols, join_symbol=" ")
  else:
    assert False


def split_interval_symbols(symbols: Symbols, intervals_interval_format: IntervalFormat, join_symbols: Optional[Set[Symbol]], ignore_join_symbols: Optional[Set[Symbol]]) -> Generator[Symbols, None, None]:
  assert has_lower_format(intervals_interval_format)
  target_format = get_lower_format(intervals_interval_format)
  marks: Generator[Symbols, None, None] = None
  if target_format == IntervalFormat.WORD:
    marks = symbols_split_iterable(symbols, split_symbols=" ")
  elif target_format == IntervalFormat.SYMBOLS:
    if join_symbols is not None:
      ignore_merge_symbols = set()
      if ignore_join_symbols is not None:
        ignore_merge_symbols = ignore_join_symbols

      # TODO group instead of merge
      symbols = merge_right(
        symbols=symbols,
        ignore_merge_symbols=ignore_merge_symbols,
        merge_symbols=join_symbols,
        insert_symbol=" ",
      )

      symbols = merge_left(
        symbols=symbols,
        ignore_merge_symbols=ignore_merge_symbols,
        merge_symbols=join_symbols,
        insert_symbol=" ",
      )

      marks = (
        convert_symbols_string_to_symbols(symbol_str)
        for symbol_str in symbols
      )
    else:
      marks = (tuple(symbol) for symbol in symbols)
  elif target_format == IntervalFormat.SYMBOL:
    marks = (tuple(symbol) for symbol in symbols)
  else:
    assert False
  marks = (symbols for symbols in marks if len(symbols) > 0)
  return marks


def has_lower_format(interval_format: IntervalFormat) -> bool:
  nr = int(interval_format)
  prv_nr = nr - 1
  result = prv_nr >= 0
  return result


def get_lower_format(interval_format: IntervalFormat) -> IntervalFormat:
  assert has_lower_format(interval_format)
  number = int(interval_format)
  prv_nr = number - 1
  result = list(IntervalFormat)[prv_nr]
  return result


def get_upper_format(interval_format: IntervalFormat) -> IntervalFormat:
  all_formats = list(IntervalFormat)
  is_last = interval_format == all_formats[-1]
  if is_last:
    return interval_format

  number = int(interval_format)
  next_nr = number + 1
  result = all_formats[next_nr]
  return result
