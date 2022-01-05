from enum import IntEnum
from typing import Collection

from text_utils.types import Symbols
from text_utils.utils import symbols_join


class IntervalFormat(IntEnum):
  SYMBOL = 0
  SYMBOLS = 1
  WORD = 2
  WORDS = 3

  def __str__(self) -> str:
    if self == self.SYMBOL:
      return "SYMBOL"

    if self == self.SYMBOLS:
      return "SYMBOLS"

    if self == self.WORD:
      return "WORD"

    if self == self.WORDS:
      return "WORDS"

    assert False

  def join_symbols(self, symbols: Collection[Symbols]) -> Symbols:
    return join_symbols(symbols, self)


def join_symbols(symbols: Collection[Symbols], symbols_format: IntervalFormat) -> Symbols:
  if symbols_format in (IntervalFormat.WORD, IntervalFormat.WORDS):
    join_symbol = " "
  elif symbols_format in (IntervalFormat.SYMBOL, IntervalFormat.SYMBOLS):
    join_symbol = None
  else:
    assert False

  joined_symbols = symbols_join(symbols, join_symbol=join_symbol)
  return joined_symbols
