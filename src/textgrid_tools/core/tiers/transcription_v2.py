from logging import getLogger
import random
from textgrid import Interval
from typing import Generator, Iterable, Optional, Set, cast

from pronunciation_dictionary import PronunciationDict, Word, get_weighted_pronunciation
from textgrid.textgrid import TextGrid
from textgrid_tools.core.comparison import check_intervals_are_equal
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.helper import (get_all_tiers, get_mark,
                                        interval_is_None_or_empty)
from textgrid_tools.core.intervals.common import replace_intervals
from textgrid_tools.core.validation import (InvalidGridError,
                                            NotExistingTierError,
                                            ValidationError)


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


def transcribe_text_v2(grid: TextGrid, tier_names: Set[str], pronunciation_dictionary: PronunciationDict, seed: Optional[int]) -> ExecutionResult:
  """
  chunksize: amount of intervals at once
  """
  assert len(tier_names) > 0

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
        splitted_intervals = list(get_split_intervals(interval, pronunciation_dictionary, seed))
      except VocabularyMissingError as error:
        return error, False

      if not check_intervals_are_equal([interval], splitted_intervals):
        replace_intervals(tier, [interval], splitted_intervals)
        changed_anything = True

  return None, changed_anything


def get_split_intervals(interval: Interval, pronunciation_dictionary: PronunciationDict, seed: Optional[int]) -> Generator[Interval, None, None]:
  if interval_is_None_or_empty(interval):
    yield interval
    return

  mark = get_mark(interval)
  if error := VocabularyMissingError.validate(mark, pronunciation_dictionary):
    logger = getLogger(__name__)
    logger.debug(interval)
    raise error

  phonemes = get_weighted_pronunciation(mark, pronunciation_dictionary, seed)
  assert len(phonemes) > 0

  count_of_symbols = len(phonemes)
  current_timepoint = interval.minTime
  interval_duration = interval.duration()
  phoneme_duration = interval_duration / count_of_symbols

  for i, phoneme in enumerate(phonemes):
    assert len(phoneme) > 0

    min_time = current_timepoint
    is_last = i == len(phonemes) - 1
    if is_last:
      max_time = interval.maxTime
    else:
      max_time = current_timepoint + phoneme_duration

    assert min_time < max_time

    new_interval = Interval(
      minTime=min_time,
      maxTime=max_time,
      mark=phoneme,
    )

    current_timepoint = max_time
    yield new_interval
