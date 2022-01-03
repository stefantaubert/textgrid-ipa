from enum import IntEnum
from logging import getLogger
from typing import (Generator, Iterable, Iterator, List, Optional, Set, Tuple,
                    cast)

from text_utils import Language, text_to_sentences
from text_utils.symbol_format import SymbolFormat
from text_utils.utils import symbols_strip
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    get_boundary_timepoints_from_tier, get_first_tier,
    get_intervals_part_of_timespan, interval_is_None_or_empty,
    intervals_to_text, tier_exists, tier_to_text)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from textgrid_tools.core.mfa.string_format import (SYMBOLS_SEPARATOR,
                                                   StringFormat)
from textgrid_tools.utils import durations_to_intervals, update_or_add_tier


class JoinMode(IntEnum):
  TIER = 0
  BOUNDARY = 1
  PAUSE = 2
  SENTENCE = 3

  def __str__(self) -> str:
    if self == self.TIER:
      return "TIER"

    if self == self.BOUNDARY:
      return "BOUNDARY"

    if self == self.PAUSE:
      return "PAUSE"

    if self == self.SENTENCE:
      return "SENTENCE"

    assert False


def can_join_intervals(grid: TextGrid, tier: str, new_tier: str, min_pause_s: Optional[float], boundary_tier: Optional[str], mode: JoinMode, overwrite_tier: bool) -> None:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier):
    logger.error(f"Tier \"{tier}\" not found!")
    return False

  if tier_exists(grid, new_tier) and not overwrite_tier:
    logger.error(f"Tier \"{new_tier}\" already exists!")
    return False

  if mode == JoinMode.BOUNDARY:
    if boundary_tier is None:
      logger.error("No reference tier defined!")
      return False

    if not tier_exists(grid, boundary_tier):
      logger.error(f"Reference tier \"{boundary_tier}\" not found!")
      return False

    tier_instance = get_first_tier(grid, tier)
    b_tier = get_first_tier(grid, boundary_tier)
    synchronize_timepoints = get_boundary_timepoints_from_tier(b_tier)

    all_tiers_share_timepoints = check_timepoints_exist_on_all_tiers_as_boundaries(
      synchronize_timepoints, [tier_instance])

    if not all_tiers_share_timepoints:
      logger.error(f"Not all boundaries of tier \"{boundary_tier}\" exist on tier \"{tier}\"!")
      return False

  if mode == JoinMode.TIER:
    pass

  if mode == JoinMode.PAUSE:
    if min_pause_s is None:
      logger.error("No min pause defined!")
      return False

    if min_pause_s <= 0:
      logger.error("Min pause needs to be > 0!")
      return False

  if mode == JoinMode.SENTENCE:
    pass

  return True


def join_intervals(grid: TextGrid, tier: str, tier_string_format: StringFormat, new_tier: str, min_pause_s: Optional[float], boundary_tier: Optional[str], mode: JoinMode, overwrite_tier: bool) -> None:
  assert can_join_intervals(grid, tier, new_tier,
                            min_pause_s, boundary_tier, mode, overwrite_tier)

  tier_instance = get_first_tier(grid, tier)

  interval_iterator: Iterator[Interval] = None

  if mode == JoinMode.PAUSE:
    interval_iterator = join_via_pause(tier_instance, min_pause_s)
  elif mode == JoinMode.TIER:
    interval_iterator = join_whole_tier(tier_instance, tier_string_format)
  elif mode == JoinMode.BOUNDARY:
    b_tier = get_first_tier(grid, boundary_tier)
    interval_iterator = join_via_boundary(tier_instance, tier_string_format, b_tier)
  else:
    assert False

  new_tier_instance = IntervalTier(
    name=new_tier,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  for interval in interval_iterator:
    new_tier_instance.addInterval(interval)

  if overwrite_tier:
    update_or_add_tier(grid, new_tier_instance)
  else:
    grid.append(new_tier)


def join_via_sentences_v2(tier: IntervalTier, tier_string_format: StringFormat, interval_format: IntervalFormat, strip_symbols: Set[str], punctuation_symbols: Set[str]) -> Generator[Interval, None, None]:
  assert interval_format in {IntervalFormat.WORDS, IntervalFormat.WORD}
  current_sentence = []
  all_sentences = []
  for interval in tier.intervals:
    interval_is_pause_between_sentences = len(
      current_sentence) == 0 and interval_is_None_or_empty(interval)

    if interval_is_pause_between_sentences:
      all_sentences.append([interval])
      continue

    current_sentence.append(interval)
    current_interval_tuple = interval_to_tuple(interval, tier_string_format)
    interval_content = symbols_strip(current_interval_tuple, strip={""} | strip_symbols)
    is_ending = symbols_endswith(interval_content, punctuation_symbols)
    if is_ending:
      all_sentences.append(current_sentence)
      current_sentence = []

  for sentence in all_sentences:
    yield merge_intervals(sentence, tier_string_format)


def merge_intervals(intervals: Iterable[Interval], tier_string_format: StringFormat) -> Interval:
  assert len(intervals) > 0
  first_interval = intervals[0]
  last_interval = intervals[-1]
  is_pause = len(intervals) == 1 and interval_is_None_or_empty(intervals[0])
  if is_pause:
    mark = intervals[0].mark
  else:
    mark = intervals_to_text(
      intervals, tier_string_format.get_word_separator(), strip=False)
  interval = Interval(
    minTime=first_interval.minTime,
    maxTime=last_interval.maxTime,
    mark=mark,
  )
  return interval


def symbols_endswith(symbols: Tuple[str, ...], endswith: Set[str]) -> bool:
  if len(symbols) == 0:
    return False
  last_symbol = symbols[-1]
  result = last_symbol in endswith
  return result


def join_via_sentences(tier: IntervalTier, tier_string_format: StringFormat, symbol_format: SymbolFormat, language: Language) -> Generator[Interval, None, None]:
  interval_tuples = intervals_to_tuples(tier.intervals, tier_string_format)
  text = tuples_intervals_to_text(interval_tuples)
  sentences = text_to_sentences(text, symbol_format, language)
  intervals = iter(tier.intervals)

  sentences_intervals = []
  sentence_intervals = []
  current_sentence = ""
  for sentence in sentences:
    assert len(sentence) > 0
    while True:
      try:
        current_interval = next(intervals)
      except StopIteration:
        if len(sentence_intervals) > 0:
          sentences_intervals.append(sentence_intervals)
          sentence_intervals.clear()
        break

      current_interval_tuple = interval_to_tuple(current_interval, tier_string_format)

      interval_content = symbols_strip(current_interval_tuple, strip={" ", ""})
      interval_content_text = ''.join(interval_content)
      if sentence.startswith(current_sentence + " " + interval_content_text):
        sentence_intervals.append(current_interval)
        current_sentence += interval_content_text
        if sentence == current_sentence:
          sentences_intervals.append(sentence_intervals)
          sentence_intervals.clear()
          current_sentence = ""
      else:
        raise Exception()
        # sentences_intervals.append(sentence_intervals)
        #sentence_intervals = [current_interval]
        # break

  for sentence_intervals in sentences_intervals:

    pass


def tuples_intervals_to_text(intervals: Iterable[Tuple[str, ...]]) -> str:
  tmp = []
  for interval_tuple in intervals:
    interval_content = symbols_strip(interval_tuple, strip={" ", ""})
    if len(interval_content) == 0:
      continue
    interval_text = ''.join(interval_content)
    tmp.append(interval_text)
  result = ' '.join(tmp)
  return result


def intervals_to_tuples(intervals: Iterable[Interval], string_format: StringFormat) -> Iterable[Tuple[str, ...]]:
  for interval in intervals:
    yield interval_to_tuple(interval, string_format)


def interval_to_text(interval: Interval, string_format: StringFormat) -> str:
  current_interval_tuple = interval_to_tuple(interval, string_format)
  interval_content = symbols_strip(current_interval_tuple, strip={" ", ""})
  interval_text = ''.join(interval_content)
  return interval_text


def interval_to_tuple(interval: Interval, string_format: StringFormat) -> Tuple[str, ...]:
  if interval is None:
    return tuple()

  interval_text: str = interval.mark

  if string_format == StringFormat.SYMBOLS:
    result = tuple(interval_text.split(SYMBOLS_SEPARATOR))
  elif string_format == StringFormat.TEXT:
    result = tuple(interval_text)
  else:
    assert False

  return result


def join_whole_tier(tier: IntervalTier, tier_string_format: StringFormat) -> Generator[Interval, None, None]:
  text = tier_to_text(tier, join_with=tier_string_format.get_word_separator())
  interval = Interval(
    minTime=tier.minTime,
    maxTime=tier.maxTime,
    mark=text,
  )
  yield interval


def join_via_boundary(tier: IntervalTier, tier_string_format: StringFormat, boundary_tier: IntervalTier) -> Generator[Interval, None, None]:
  synchronize_timepoints = get_boundary_timepoints_from_tier(boundary_tier)

  for i in range(1, len(synchronize_timepoints)):
    last_timepoint = synchronize_timepoints[i - 1]
    current_timepoint = synchronize_timepoints[i]
    tier_intervals_in_range = list(get_intervals_part_of_timespan(
      tier, last_timepoint, current_timepoint))
    sep = tier_string_format.get_word_separator()
    # TODO join right!
    content = intervals_to_text(tier_intervals_in_range, join_with=sep)
    new_interval = Interval(
      minTime=last_timepoint,
      maxTime=current_timepoint,
      mark=content,
    )
    yield new_interval


def join_via_pause(tier: IntervalTier, min_pause_s: float) -> Generator[Interval, None, None]:
  durations: List[Tuple[str, float]] = []
  current_batch = []
  current_duration = 0
  interval: Interval
  for interval in tier.intervals:
    is_empty = interval_is_None_or_empty(interval)
    if is_empty:
      if interval.duration() < min_pause_s:
        current_duration += interval.duration()
      else:
        if len(current_batch) > 0:
          batch_str = " ".join(current_batch)
          durations.append((batch_str, current_duration))
          current_batch.clear()
          current_duration = 0
        durations.append((interval.mark, interval.duration()))
    else:
      current_batch.append(interval.mark)
      current_duration += interval.duration()

  if len(current_batch) > 0:
    batch_str = " ".join(current_batch)
    durations.append((batch_str, current_duration))

  intervals = durations_to_intervals(durations, maxTime=tier.maxTime)
  return iter(intervals)
