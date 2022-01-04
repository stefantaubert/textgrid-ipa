from enum import IntEnum
from logging import getLogger
from typing import (Generator, Iterable, Iterator, List, Optional, Set, Tuple,
                    cast)

from text_utils import (SYMBOLS_SEPARATOR, Language, StringFormat,
                        text_to_sentences)
from text_utils.string_format import join_strings, string_to_str
from text_utils.symbol_format import SymbolFormat
from text_utils.utils import symbols_strip
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (
    check_is_valid_grid, check_timepoints_exist_on_all_tiers_as_boundaries,
    get_boundary_timepoints_from_tier, get_first_tier,
    get_intervals_part_of_timespan, interval_is_None_or_whitespace,
    intervals_to_text, tier_exists, tier_to_text)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
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


def join_intervals(grid: TextGrid, tier: str, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, new_tier: str, min_pause_s: Optional[float], boundary_tier: Optional[str], mode: JoinMode, overwrite_tier: bool) -> None:
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
    interval_iterator = join_via_boundary(
      tier_instance, tier_string_format, tier_interval_format, b_tier)
  elif mode == JoinMode.SENTENCE:
    interval_iterator = join_via_sentences(
      tier_instance, tier_string_format, IntervalFormat.WORD, {}, {})
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
    grid.append(new_tier_instance)


def join_via_sentences(tier: IntervalTier, tier_string_format: StringFormat, interval_format: IntervalFormat, strip_symbols: Set[str], punctuation_symbols: Set[str]) -> Generator[Interval, None, None]:
  assert interval_format in {IntervalFormat.WORDS, IntervalFormat.WORD}
  current_sentence = []
  all_sentences = []
  for interval in tier.intervals:
    interval_is_pause_between_sentences = len(
      current_sentence) == 0 and interval_is_None_or_whitespace(interval)

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
  is_pause = len(intervals) == 1 and interval_is_None_or_whitespace(intervals[0])
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


def join_via_boundary(tier: IntervalTier, tier_string_format: StringFormat, tier_interval_format: IntervalFormat, boundary_tier: IntervalTier) -> Generator[Interval, None, None]:
  synchronize_timepoints = get_boundary_timepoints_from_tier(boundary_tier)
  # tier_interval_format is also the target string_format
  if tier_string_format == StringFormat.SYMBOLS:
    if tier_interval_format in {IntervalFormat.WORD, IntervalFormat.WORDS}:
      sep = tier_string_format.get_word_separator()
    elif tier_interval_format == IntervalFormat.SYMBOL:
      sep = SYMBOLS_SEPARATOR
    else:
      assert False
  elif tier_string_format == StringFormat.TEXT:
    if tier_interval_format in {IntervalFormat.WORD, IntervalFormat.WORDS}:
      sep = " "
    elif tier_interval_format == IntervalFormat.SYMBOL:
      sep = ""
    else:
      assert False
  else:
    assert False

  strip = True

  for i in range(1, len(synchronize_timepoints)):
    last_timepoint = synchronize_timepoints[i - 1]
    current_timepoint = synchronize_timepoints[i]
    tier_intervals_in_range = list(get_intervals_part_of_timespan(
      tier, last_timepoint, current_timepoint))
    entrys = []
    for interval in tier_intervals_in_range:

      if interval is None:
        continue
      interval_text: str = interval.mark
      if strip:
        interval_text = interval_text.strip()
      if len(interval_text) == 0:
        continue
      if not tier_string_format.can_parse_string(interval_text):
        raise Exception()
      string = tier_string_format.parse_string(interval_text)
      entrys.append(string)

    content = join_strings(entrys, sep)
    mark = string_to_str(content)
    #content = intervals_to_text(tier_intervals_in_range, join_with=sep)
    new_interval = Interval(
      minTime=last_timepoint,
      maxTime=current_timepoint,
      mark=mark,
    )
    yield new_interval


def join_via_pause(tier: IntervalTier, min_pause_s: float) -> Generator[Interval, None, None]:
  durations: List[Tuple[str, float]] = []
  current_batch = []
  current_duration = 0
  interval: Interval
  for interval in tier.intervals:
    is_empty = interval_is_None_or_whitespace(interval)
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
