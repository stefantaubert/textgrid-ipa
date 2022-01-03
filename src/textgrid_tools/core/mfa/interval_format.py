from enum import IntEnum


class IntervalFormat(IntEnum):
  SYMBOL = 0
  WORD = 1
  WORDS = 2

  def __str__(self) -> str:
    if self == self.SYMBOL:
      return "SYMBOL"

    if self == self.WORD:
      return "WORD"

    if self == self.WORDS:
      return "WORDS"

    assert False
