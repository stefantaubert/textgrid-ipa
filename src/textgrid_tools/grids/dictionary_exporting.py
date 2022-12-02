from collections import Counter, OrderedDict
from logging import Logger, getLogger
from typing import Dict, Iterable, List, Literal, Optional, Set, Tuple, Union

from pronunciation_dictionary import PronunciationDict
from textgrid import Interval, TextGrid

from textgrid_tools.helper import (get_boundary_timepoints_from_intervals, get_interval_readable,
                                   get_intervals_on_tier, get_single_tier, ignore_intervals_by_mark)
from textgrid_tools.validation import (BoundaryError, InvalidGridError, NonDistinctTiersError,
                                       NotExistingTierError, ValidationError)


class IntervalContainsSpaceError(ValidationError):
  def __init__(self, interval: Interval) -> None:
    super().__init__()
    self.interval = interval

  @classmethod
  def validate(cls, interval: Interval):
    if " " in interval.mark:
      return cls(interval)
    return None

  @property
  def default_message(self) -> str:
    return f"Interval contains space!\n{get_interval_readable(self.interval)}"


def create_dictionaries(grids: Dict[str, List[TextGrid]], words_tier_name: str, pronunciations_tier_name: str, scope: Optional[Literal["folder", "all"]], ignore_marks: Set[str], logger: Optional[Logger]) -> Tuple[Optional[ValidationError], Union[PronunciationDict, Dict[str, PronunciationDict]]]:
  if logger is None:
    logger = getLogger(__name__)
  speakers_pronunciations: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {}
  for speaker_name, speaker_grids in grids.items():
    speaker_pronunciations: List[Tuple[str, Tuple[str, ...]]] = []
    for grid in speaker_grids:
      if error := InvalidGridError.validate(grid):
        return error, False

      if error := NotExistingTierError.validate(grid, words_tier_name):
        return error, False

      if error := NonDistinctTiersError.validate(words_tier_name, pronunciations_tier_name):
        return error, False

      if error := NotExistingTierError.validate(grid, pronunciations_tier_name):
        return error, False

      words_tier = get_single_tier(grid, words_tier_name)
      words_tier_intervals = list(ignore_intervals_by_mark(words_tier.intervals, ignore_marks))
      pronunciation_tier = get_single_tier(grid, pronunciations_tier_name)

      words_tier_timepoints = get_boundary_timepoints_from_intervals(words_tier_intervals)
      if error := BoundaryError.validate(words_tier_timepoints, [pronunciation_tier]):
        return error, False

      for word_interval in words_tier_intervals:
        if error := IntervalContainsSpaceError.validate(word_interval):
          return error, False

        word = word_interval.mark
        pronunciation_intervals = get_intervals_on_tier(word_interval, pronunciation_tier)
        for interval in pronunciation_intervals:
          if error := IntervalContainsSpaceError.validate(interval):
            return error, False
        pronunciation = tuple(interval.mark for interval in pronunciation_intervals)
        speaker_pronunciations.append((word, pronunciation))
    speakers_pronunciations[speaker_name] = speaker_pronunciations

  if scope == "all":
    pronunciations = (entry for p in speakers_pronunciations.values() for entry in p)
    result = get_dict_from_pronunciations(pronunciations)
  elif scope == "folder":
    result: Dict[str, PronunciationDict] = {}
    for speaker_name, pronunciations in speakers_pronunciations.items():
      result[speaker_name] = get_dict_from_pronunciations(pronunciations)
  else:
    assert False

  return None, result


def get_dict_from_pronunciations(pronunciations: Iterable[Tuple[str, Tuple[str, ...]]]) -> PronunciationDict:
  dictionary: PronunciationDict = OrderedDict()
  weights = Counter(pronunciations)
  # sort after word and then descending after weight and then after pronunciation
  sorted_pronunciations = sorted(
    weights.items(), key=lambda wp_w: (wp_w[0][0], -wp_w[1], wp_w[0][1]))
  for (word, pronunciation), weight in sorted_pronunciations:
    if word not in dictionary:
      dictionary[word] = OrderedDict()
    dictionary[word][pronunciation] = weight
  return dictionary
