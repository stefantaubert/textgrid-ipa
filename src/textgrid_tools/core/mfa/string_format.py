from enum import IntEnum
from typing import List, Tuple

from text_utils.utils import symbols_join

SYMBOLS_SEPARATOR = " "
SYMBOLS_WORD_SEPARATOR = "  "
TEXT_WORD_SEPARATOR = " "


class StringFormat(IntEnum):
  TEXT = 0
  SYMBOLS = 1

  def get_word_separator(self) -> str:
    if self == StringFormat.TEXT:
      return " "
    if self == StringFormat.SYMBOLS:
      return SYMBOLS_WORD_SEPARATOR
    assert False

  def get_words(self, text: str) -> List[str]:
    if self == StringFormat.SYMBOLS:
      assert can_parse_text(text)
    words = text.split(sep=self.get_word_separator())
    return words


def get_symbols(text: str) -> Tuple[str, ...]:
  result = tuple(text.split(SYMBOLS_SEPARATOR))
  return result


def can_parse_text(text: str) -> bool:
  result = "   " not in text
  return result


def transform_text_to_symbols(text: str) -> str:
  words = StringFormat.TEXT.get_words(text)
  words_symbols = [tuple(list(word)) for word in words]
  symbols = symbols_join(words_symbols, join_symbol=SYMBOLS_WORD_SEPARATOR)
  symbols_str = ''.join(symbols)
  return symbols_str
