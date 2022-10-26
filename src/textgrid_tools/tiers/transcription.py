from logging import Logger, getLogger
from typing import Generator, Iterable, Optional, Set, cast

from pronunciation_dictionary import PronunciationDict, get_weighted_pronunciation
from textgrid import Interval, TextGrid

from textgrid_tools.comparison import check_intervals_are_equal
from textgrid_tools.globals import ExecutionResult
from textgrid_tools.helper import (get_all_tiers, get_interval_readable, get_mark,
                                   interval_is_None_or_empty, set_intervals_consecutive)
from textgrid_tools.intervals.common import replace_intervals
from textgrid_tools.validation import InvalidGridError, NotExistingTierError, ValidationError


class VocabularyMissingError(ValidationError):
  def __init__(self, word: str, dictionary: PronunciationDict) -> None:
    super().__init__()
    self.word = word
    self.dictionary = dictionary

  @classmethod
  def validate(cls, word: str, dictionary: PronunciationDict):
    if not word in dictionary:
      return cls(word, dictionary)
    return None

  @property
  def default_message(self) -> str:
    return f"Dictionary does not contain '{self.word}'"


# class MissingWordsInDictError(ValidationError):
#   def __init__(self, dictionary: PronunciationDict, missing: OrderedSet[Word]) -> None:
#     super().__init__()
#     self.dictionary = dictionary
#     self.missing = missing

#   @classmethod
#   def validate(cls, dictionary: PronunciationDict, words: OrderedSet[Word]):
#     vocabulary = OrderedSet(dictionary.keys())
#     missing = words.difference(vocabulary)
#     if not len(missing) == 0:
#       return cls(dictionary, missing)
#     return None

#   @property
#   def default_message(self) -> str:
#     return f"{len(self.missing)} words are missing in the pronunciation dictionary!"


def transcribe_text(grid: TextGrid, tier_names: Set[str], pronunciation_dictionary: PronunciationDict, seed: Optional[int], ignore_missing: bool, replace_missing: Optional[str], logger: Optional[Logger]) -> ExecutionResult:
  # TODO add mode first, last etc
  """
  chunksize: amount of intervals at once
  """
  assert len(tier_names) > 0

  if logger is None:
    logger = getLogger(__name__)

  if error := InvalidGridError.validate(grid):
    return error, False

  for tier_name in tier_names:
    if error := NotExistingTierError.validate(grid, tier_name):
      return error, False

  tiers = list(get_all_tiers(grid, tier_names))

  for tier in tiers:
    intervals_copy = cast(Iterable[Interval], list(tier.intervals))
    for interval in intervals_copy:
      try:
        splitted_intervals = list(get_split_intervals(
          interval, pronunciation_dictionary, seed, ignore_missing, replace_missing, logger))
      except VocabularyMissingError as error:
        return error, False

      if not check_intervals_are_equal([interval], splitted_intervals):
        replace_intervals(tier, [interval], splitted_intervals)
        changed_anything = True

  return None, changed_anything


def get_split_intervals(interval: Interval, pronunciation_dictionary: PronunciationDict, seed: Optional[int], ignore_missing: bool, replace_missing: Optional[str], logger: Logger) -> Generator[Interval, None, None]:
  if interval_is_None_or_empty(interval):
    yield interval
    return

  mark = get_mark(interval)
  if error := VocabularyMissingError.validate(mark, pronunciation_dictionary):
    if ignore_missing:
      if replace_missing is None:
        logger.info(f"Kept unchanged: {get_interval_readable(interval)}")
        yield interval
        return
      else:
        new_interval = Interval(interval.minTime, interval.maxTime, replace_missing)
        yield new_interval
        return

    logger.debug(interval)
    raise error

  pronunciations = pronunciation_dictionary[mark]
  phonemes = get_weighted_pronunciation(pronunciations, seed)
  assert len(phonemes) > 0

  new_intervals = [
    Interval(0, 1, phoneme)
    for phoneme in phonemes
  ]

  set_intervals_consecutive(new_intervals, interval.minTime, interval.maxTime)
  yield from new_intervals
