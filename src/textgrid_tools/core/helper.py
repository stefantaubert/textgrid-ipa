from typing import Generator, Iterable, List, Optional, Set, cast

from ordered_set import OrderedSet
from text_utils import StringFormat, symbols_ignore
from text_utils.types import Symbols
from textgrid.textgrid import Interval, IntervalTier, TextGrid


def get_intervals_duration(intervals: Iterable[Interval]) -> float:
  durations = (interval.duration() for interval in intervals)
  result = sum(durations)
  return result


def set_precision_grid(grid: TextGrid, n_digits: int) -> None:
  grid.minTime = round(grid.minTime, n_digits)
  grid.maxTime = round(grid.maxTime, n_digits)
  for tier in grid.tiers:
    set_precision_tier(tier, n_digits)


def set_precision_tier(tier: IntervalTier, n_digits: int) -> None:
  tier.minTime = round(tier.minTime, n_digits)
  tier.maxTime = round(tier.maxTime, n_digits)
  for interval in tier.intervals:
    set_precision_interval(interval, n_digits)


def set_precision_interval(interval: Interval, n_digits: int) -> None:
  interval.minTime = round(interval.minTime, n_digits)
  interval.maxTime = round(interval.maxTime, n_digits)


def check_is_valid_grid(grid: TextGrid) -> bool:
  if grid.minTime is None or grid.maxTime is None:
    return False

  if not check_minTime_and_maxTime_are_valid(grid.minTime, grid.maxTime):
    return False

  for tier in grid.tiers:
    if not do_tier_boundaries_match_those_from_grid(tier, grid):
      return False

    if not is_tier_valid(tier):
      return False
  return True


def do_tier_boundaries_match_those_from_grid(tier: IntervalTier, grid: TextGrid) -> bool:
  if tier.minTime != grid.minTime:
    return False
  if tier.maxTime != grid.maxTime:
    return False
  return True


def do_interval_boundaries_match_those_from_tier(tier: IntervalTier) -> bool:
  if len(tier.intervals) > 0:
    first_interval = tier.intervals[0]
    last_interval = tier.intervals[-1]
    if tier.minTime != first_interval.minTime:
      return False
    if tier.maxTime != last_interval.maxTime:
      return False
  return True


def check_minTime_and_maxTime_are_valid(min_time: float, max_time: float) -> bool:
  if not (min_time < max_time):
    return False
  if min_time < 0 or max_time <= 0:
    return False
  return True


def is_tier_valid(tier: IntervalTier) -> bool:
  if not check_minTime_and_maxTime_are_valid(tier.minTime, tier.maxTime):
    return False

  if not check_tier_intervals_are_consecutive(tier):
    return False

  for interval in tier.intervals:
    if not check_interval_is_valid(interval):
      return False

  if not do_interval_boundaries_match_those_from_tier(tier):
    return False
  return True


def check_interval_is_valid(interval: Interval) -> bool:
  return check_minTime_and_maxTime_are_valid(interval.minTime, interval.maxTime)


def check_tier_intervals_are_consecutive(tier: IntervalTier) -> bool:
  for i in range(1, len(tier.intervals)):
    prev_interval = cast(Interval, tier.intervals[i - 1])
    current_interval = cast(Interval, tier.intervals[i])
    if prev_interval.maxTime != current_interval.minTime:
      return False
  return True


def timepoint_is_boundary(timepoint: float, tier: IntervalTier) -> bool:
  min_time_interval = get_interval_from_minTime(tier, timepoint)
  if min_time_interval is not None:
    return True
  max_time_interval = get_interval_from_maxTime(tier, timepoint)
  if max_time_interval is not None:
    # it is the last interval
    return True
  return False


def get_mark(interval: Interval) -> str:
  if interval.mark is None:
    return ""
  return interval.mark


def get_mark_symbols(interval: Interval, string_format: StringFormat) -> Symbols:
  return string_format.convert_string_to_symbols(get_mark(interval))


def get_mark_symbols_intervals(intervals: Iterable[Interval], string_format: StringFormat) -> Generator[Symbols, None, None]:
  for interval in intervals:
    yield get_mark_symbols(interval, string_format)


def symbols_are_empty_or_whitespace(symbols: Symbols) -> bool:
  result = symbols_ignore(symbols, ignore={" ", ""})
  return len(result) == 0


def str_is_empty_or_whitespace(string: str) -> bool:
  return string.strip() == ""


def get_interval_readable(interval: Interval) -> str:
  result = f"Interval [{interval.minTime}, {interval.maxTime}]: \"{get_mark(interval)}\""
  return result


def get_tier_readable(tier: IntervalTier) -> str:
  result = f"Tier [{tier.minTime}, {tier.maxTime}]: \"{tier.name}\" (# intervals: {len(tier.intervals)})"
  return result


def get_interval_from_minTime(tier: IntervalTier, minTime: float) -> Optional[Interval]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.minTime == minTime:
      return interval
  return None


def get_interval_from_maxTime(tier: IntervalTier, maxTime: float) -> Optional[Interval]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if interval.maxTime == maxTime:
      return interval
  return None


def get_intervals_from_timespan(tier: IntervalTier, minTime: float, maxTime: float) -> Generator[Interval, None, None]:
  for interval in cast(Iterable[Interval], tier.intervals):
    if minTime <= interval.minTime and interval.maxTime <= maxTime:
      yield interval


def get_intervals_on_tier(interval: Interval, tier: IntervalTier) -> List[Interval]:
  result = list(get_intervals_from_timespan(tier, interval.minTime, interval.maxTime))
  assert len(result) > 0
  assert result[0].minTime == interval.minTime
  assert result[-1].maxTime == interval.maxTime
  return result


def get_intervals_part_of_timespan(tier: IntervalTier, min_time: float, max_time: float) -> Generator[Interval, None, None]:
  # intervals where interval.maxTime = minTime were not considered
  # intervals where interval.minTime = maxTime were not considered
  for interval in cast(Iterable[Interval], tier.intervals):
    min_time_lies_in_span = min_time <= interval.minTime and interval.minTime < max_time
    max_time_lies_in_span = min_time < interval.maxTime and interval.maxTime <= max_time
    if min_time_lies_in_span or max_time_lies_in_span:
      yield interval


def check_timepoints_exist_on_all_tiers_as_boundaries(timepoints: List[float], tiers: List[IntervalTier]) -> bool:
  result = True
  for timepoint in timepoints:
    result &= check_timepoint_exist_on_all_tiers_as_boundary(timepoint, tiers)
  return result


def get_count_of_tiers(grid: TextGrid, tier_name: str) -> int:
  tiers = list(get_all_tiers(grid, {tier_name}))
  return len(tiers)


def get_single_tier(grid: TextGrid, tier_name: str) -> IntervalTier:
  tiers = list(get_all_tiers(grid, {tier_name}))
  if len(tiers) > 1:
    assert False
  return tiers[0]


def can_parse_float(float_str: str) -> bool:
  try:
    float(float_str)
    return True
  except ValueError:
    return False


def get_all_intervals(grid: TextGrid, tier_names: Set[str]) -> Generator[Interval, None, None]:
  intervals = (
    interval
    for tier in get_all_tiers(grid, tier_names)
    for interval in cast(Iterable[Interval], tier.intervals)
  )
  return intervals


def get_all_tiers(grid: TextGrid, tier_names: Set[str]) -> Generator[IntervalTier, None, None]:
  for tier in cast(Iterable[IntervalTier], grid.tiers):
    if tier.name in tier_names:
      yield tier


# def get_first_tier(grid: TextGrid, tier_name: str) -> IntervalTier:
#   assert tier_exists(grid, tier_name)
#   return next(get_all_tiers(grid, {tier_name}))


def tier_exists(grid: TextGrid, tier: str) -> bool:
  tiers = get_all_tiers(grid, {tier})
  for _ in tiers:
    return True
  return False


# def add_or_update_tier(grid: TextGrid, tier: Optional[IntervalTier], output_tier: IntervalTier, overwrite_tier: bool) -> bool:
#   if overwrite_tier and tier is not None and tier.name == output_tier.name:
#     if not check_tiers_are_equal(tier, output_tier):
#       replace_tier(tier, output_tier)
#       return True
#   elif overwrite_tier and tier_exists(grid, output_tier.name):
#     existing_tier = get_first_tier(grid, output_tier.name)
#     if not check_tiers_are_equal(existing_tier, output_tier):
#       replace_tier(existing_tier, output_tier)
#       return True
#   else:
#     grid.append(output_tier)
#     return True
#   return False


def replace_tier(tier: IntervalTier, new_tier: IntervalTier) -> None:
  tier.intervals.clear()
  tier.intervals.extend(new_tier.intervals)
  tier.minTime = new_tier.minTime
  tier.maxTime = new_tier.maxTime
  tier.name = new_tier.name
  tier.strict = new_tier.strict


def check_timepoint_exist_on_all_tiers_as_boundary(timepoint: float, tiers: List[IntervalTier]) -> bool:
  result = True
  for tier in tiers:
    result &= timepoint_is_boundary(timepoint, tier)
  return result


def get_boundary_timepoints_from_tier(tier: IntervalTier) -> OrderedSet[float]:
  return get_boundary_timepoints_from_intervals(tier.intervals)


def get_boundary_timepoints_from_intervals(intervals: List[Interval]) -> OrderedSet[float]:
  result: OrderedSet[float] = OrderedSet()
  for interval in intervals:
    result.add(interval.minTime)
    result.add(interval.maxTime)
  return result


def interval_is_None_or_whitespace(interval: Interval) -> bool:
  return interval.mark is None or len(interval.mark.strip()) == 0


def interval_is_None_or_empty(interval: Interval) -> bool:
  return interval.mark is None or len(interval.mark) == 0

# def check_interval_boundaries_exist_on_all_tiers(intervals: Interval, tiers: List[IntervalTier]):
#   result = True
#   for ref_interval in intervals:
#     valid = check_boundaries_exist_on_all_tiers(ref_interval.minTime, ref_interval.maxTime, tiers)
#     if not valid:
#       result = False
#   return result


# def check_boundaries_exist_on_all_tiers(minTime: float, maxTime: float, tiers: List[IntervalTier]) -> bool:
#   result = True
#   for tier in tiers:
#     result &= check_boundaries_exist_in_tier(minTime, maxTime, tier)
#   return result


# def check_boundaries_exist_in_tier(minTime: float, maxTime: float, tier: IntervalTier) -> bool:
#   logger = getLogger(__name__)
#   corresponding_intervals = list(get_intervals_from_timespan(
#     tier, minTime, maxTime))

#   if len(corresponding_intervals) == 0:
#     logger.error(
#       f"Tier \"{tier.name}\": Interval [{minTime}, {maxTime}] does not exist!")
#     return False

#   minTime_matches = corresponding_intervals[0].minTime == minTime
#   maxTime_matches = corresponding_intervals[-1].maxTime == maxTime

#   result = True
#   if not minTime_matches:
#     logger.error(
#       f"Tier \"{tier.name}\": Start of interval [{corresponding_intervals[0].minTime}, {corresponding_intervals[0].maxTime}] (\"{corresponding_intervals[0].mark}\") does not match with start of interval [{minTime}, {maxTime}]! Difference: {corresponding_intervals[0].minTime - minTime}")
#     result = False

#   if not maxTime_matches:
#     logger.error(
#       f"Tier \"{tier.name}\": End of interval [{corresponding_intervals[-1].minTime}, {corresponding_intervals[-1].maxTime}] (\"{corresponding_intervals[-1].mark}\") does not match with end of interval [{minTime}, {maxTime}]! Difference: {corresponding_intervals[-1].maxTime - maxTime}")
#     result = False
#   return result